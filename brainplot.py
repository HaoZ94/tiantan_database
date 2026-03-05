import matplotlib
matplotlib.use("Agg")   # <- add this for headless server

import io, os, smtplib

import numpy as np
import nibabel as nib
import pandas as pd
import matplotlib.pyplot as plt

from nilearn import plotting, image
from scipy.ndimage import center_of_mass
from email.message import EmailMessage
from flask import Flask, request, send_file, jsonify

class AAL3BrainViewer:
    """
    Tools for:
      1) Given MNI XYZ of a contact:
         - check validity
         - plot 3 orthogonal MRI views centered there
         - highlight its AAL3 region
      2) Given an AAL3 region name:
         - center on its center of mass
         - plot 3 orthogonal MRI views
         - highlight the region
      3) Simple 3D visualization with nilearn (view_markers)
    """

    def __init__(
        self,
        template_img_path: str,
        aal3_atlas_img_path: str,
        aal3_labels_txt_path: str,
    ):
        # Load images
        self.template_img = nib.load(template_img_path)
        self.atlas_img = nib.load(aal3_atlas_img_path)
        self.atlas_data = self.atlas_img.get_fdata().astype(int)

        # Load the txt label file you showed (ID, name, value)
        labels_df = pd.read_csv(
            aal3_labels_txt_path,
            sep=r"\s+",
            header=None,
            names=["id", "label", "value"],
            engine="python",
        )

        # Use the first column (1..170) as atlas IDs, second as names
        labels_df["id"] = labels_df["id"].astype(int)
        labels_df["label"] = labels_df["label"].astype(str)

        self.id_to_name = dict(zip(labels_df["id"], labels_df["label"]))
        self.name_to_id = {name: idx for idx, name in self.id_to_name.items()}

        # Optional: keep a region list for menus / GUIs etc.
        self.region_names = list(self.name_to_id.keys())

    # ---------- internal helpers ----------

    def _world_to_vox(self, coord_mni):
        coord_mni = np.asarray(coord_mni, dtype=float)
        if coord_mni.shape != (3,):
            raise ValueError("coord_mni must be [x, y, z] in MNI space.")
        inv_affine = np.linalg.inv(self.atlas_img.affine)
        ijk = nib.affines.apply_affine(inv_affine, coord_mni)
        ijk = np.round(ijk).astype(int)
        return ijk  # (i, j, k)

    def _coord_inside_img(self, ijk, img):
        shape = img.shape
        return all(0 <= ijk[d] < shape[d] for d in range(3))

    # ---------- public: validity + region from coordinate ----------

    def check_coord(self, coord_mni):
        """
        Check if MNI XYZ is within the template/atlas.
        Returns a dict with:
          coord_mni, voxel_index, inside_template, inside_atlas,
          atlas_label_id, atlas_region_name
        """
        coord_mni = np.asarray(coord_mni, dtype=float)
        ijk = self._world_to_vox(coord_mni)
        inside_template = self._coord_inside_img(ijk, self.template_img)

        info = {
            "coord_mni": coord_mni.tolist(),
            "voxel_index": ijk.tolist(),
            "inside_template": bool(inside_template),
            "inside_atlas": False,
            "atlas_label_id": None,
            "atlas_region_name": None,
        }

        if inside_template:
            label_id = int(self.atlas_data[tuple(ijk)])
            info["atlas_label_id"] = label_id
            if label_id > 0:
                info["inside_atlas"] = True
                info["atlas_region_name"] = self.id_to_name.get(label_id, "Unknown")
            else:
                info["inside_atlas"] = False
                info["atlas_region_name"] = "Background / non-labeled"
        return info

    def get_region_from_coord(self, coord_mni):
        """Return (label_id, region_name) for a given MNI coordinate."""
        info = self.check_coord(coord_mni)
        if not info["inside_template"]:
            raise ValueError(
                f"Coordinate {coord_mni} is outside template volume "
                f"(voxel index {info['voxel_index']})."
            )
        return info["atlas_label_id"], info["atlas_region_name"]

    # ---------- public: center of AAL3 region ----------

    def get_region_center(self, region_name):
        """
        Given an AAL3 region name (exactly as in the txt file),
        return (center_mni [x,y,z], label_id).
        """
        if region_name not in self.name_to_id:
            raise ValueError(f"Region name '{region_name}' not found.")
        label_id = self.name_to_id[region_name]

        mask = (self.atlas_data == label_id)
        if not mask.any():
            raise ValueError(f"No voxels found for region '{region_name}' (ID={label_id}).")

        com_ijk = center_of_mass(mask.astype(float))
        center_mni = nib.affines.apply_affine(self.atlas_img.affine, com_ijk)
        return np.asarray(center_mni, dtype=float), label_id

    # ---------- public: 2D orthogonal plots ----------

    def plot_contact_views(self, coord_mni, alpha=0.4):
        """
        1) Input contact MNI XYZ, plot 3 views centered there,
           add virtual crosshair, and color the AAL3 region.
        Returns (display, region_name).
        """
        coord_mni = np.asarray(coord_mni, dtype=float)
        label_id, region_name = self.get_region_from_coord(coord_mni)

        if label_id is None or label_id == 0:
            region_name = "Background / non-labeled"
            print("WARNING: Contact in unlabeled / background atlas area.")

        mask_img = image.math_img(f"img == {int(label_id)}", img=self.atlas_img)

        title = f"{region_name} @ (x={coord_mni[0]:.1f}, y={coord_mni[1]:.1f}, z={coord_mni[2]:.1f})"
        display = plotting.plot_anat(
            self.template_img,
            display_mode="ortho",             # sagittal, coronal, axial in 3 subplots
            cut_coords=coord_mni.tolist(),    # center on the contact
            draw_cross=True,                  # virtual focus line
            annotate=False,
            title=title,
            colorbar=False
        )

        display.add_overlay(
            mask_img,
            transparency=alpha
        )

        return display, region_name

    def plot_region_views(self, region_name, alpha=0.4):
        """
        2) Input region name, center on its CoM,
           plot 3 views and color that region.
        Returns (display, center_mni).
        """
        center_mni, label_id = self.get_region_center(region_name)
        mask_img = image.math_img(f"img == {int(label_id)}", img=self.atlas_img)

        title = f"{region_name} center (x={center_mni[0]:.1f}, y={center_mni[1]:.1f}, z={center_mni[2]:.1f})"
        display = plotting.plot_anat(
            self.template_img,
            display_mode="ortho",
            cut_coords=center_mni.tolist(),
            draw_cross=True,
            annotate=False,
            title=title,
            colorbar=False
        )

        display.add_overlay(
            mask_img,
            transparency=alpha
        )

        return display, center_mni

    # ---------- public: 3D visualization ----------

    def view_contact_3d(self, coord_mni, marker_size=5):
        """
        3) 3D brain with contact marker.
        Returns a nilearn view object (display in Jupyter / save to HTML).
        """

        coord_mni = np.asarray(coord_mni, dtype=float)
        _, region_name = self.get_region_from_coord(coord_mni)

        view = plotting.view_markers(
            [coord_mni.tolist()],
            marker_size=marker_size,
            marker_color="red",
            marker_labels=[region_name]
        )
        return view

    def view_region_3d(self, region_name, threshold=0.5,alpha=0.4):
        """
        3D view highlighting the *entire* AAL3 region as a volume
        on top of the MNI template (interactive HTML viewer).

        Parameters
        ----------
        region_name : str
            AAL3 label exactly as in the txt file.
        threshold : float or str
            Intensity threshold for showing the region. For a 0/1 mask,
            something like 0.5 is fine. You can also use 'auto'.
        """

        # Get label id from name
        if region_name not in self.name_to_id:
            raise ValueError(f"Region name '{region_name}' not found.")
        label_id = self.name_to_id[region_name]

        # Build a binary mask for this region
        mask_img = image.math_img(f"img == {int(label_id)}", img=self.atlas_img)

        # Interactive 3D visualization with the mask overlaid on the template
        view = plotting.view_img(
            mask_img,
            bg_img=self.template_img,
            threshold=threshold,       # show voxels > threshold
            cmap="cyan_orange",
            symmetric_cmap=False,
            colorbar=False,
            width_view=1200,
            opacity=alpha,
            title=f"AAL3 region: {region_name}"
        )
        return view

# -------------------------------------------------------------------
# Flask backend for the website
# -------------------------------------------------------------------

# Resolve paths relative to this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
template_path = os.path.join(BASE_DIR, "assets/MNI152_T1_1mm.nii.gz")
aal3_path = os.path.join(BASE_DIR, "assets/AAL3v1_1mm.nii.gz")
labels_txt = os.path.join(BASE_DIR, "assets/AAL3v1_1mm.nii.txt")

viewer = AAL3BrainViewer(
    template_img_path=template_path,
    aal3_atlas_img_path=aal3_path,
    aal3_labels_txt_path=labels_txt,
)

app = Flask(__name__, static_url_path='', static_folder='.')

@app.route("/")
def resources_page():
    # This assumes your HTML file is named "resources.html"
    return app.send_static_file("resources.html")

@app.route("/api/regions")
def api_regions():
    """
    Return list of AAL3 region names (from AAL3v1_1mm.nii.txt).
    """
    return jsonify({"regions": viewer.region_names})


@app.route("/api/contact_plot")
def api_contact_plot():
    """
    Given MNI XYZ, return a PNG of 3 orthogonal views
    with the AAL3 region highlighted.
    """
    x = request.args.get("x", default=30.0, type=float)
    y = request.args.get("y", default=-22.0, type=float)
    z = request.args.get("z", default=55.0, type=float)
    coord = [x, y, z]

    display, region_name = viewer.plot_contact_views(coord)

    buf = io.BytesIO()
    display.savefig(buf, dpi=300, bbox_inches="tight", transparent=True)
    display.close()
    buf.seek(0)

    resp = send_file(buf, mimetype="image/png")
    # Optional: expose region name in header
    resp.headers["X-Region-Name"] = region_name
    return resp


@app.route("/api/region_plot")
def api_region_plot():
    """
    Given AAL3 region name, return a PNG centered on that region
    with the region highlighted.
    """
    region_name = request.args.get("region", type=str)
    if not region_name:
        return "Missing 'region' parameter", 400

    display, center_mni = viewer.plot_region_views(region_name)

    buf = io.BytesIO()
    display.savefig(buf, dpi=300, bbox_inches="tight", transparent=True)
    display.close()
    buf.seek(0)

    resp = send_file(buf, mimetype="image/png")
    # Optional: expose center coordinate in header
    resp.headers["X-Region-Center-MNI"] = ",".join(f"{v:.1f}" for v in center_mni)
    return resp

@app.route("/view_region_3d")
def view_region_3d_route():
    """
    Return a simple HTML page that embeds the interactive 3D viewer
    for a given AAL3 region.
    """
    region_name = request.args.get("region", type=str)
    if not region_name:
        return "Missing 'region' parameter", 400

    try:
        view = viewer.view_region_3d(region_name)
    except ValueError as e:
        return str(e), 400

    # Nilearn view object -> HTML snippet (contains its own <iframe>)
    inner_html = view._repr_html_()

    full_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>3D view: {region_name}</title>
  <style>
    html, body {{
      margin: 0;
      padding: 0;
      width: 100%;
      height: 100%;
      background: #000;
    }}
    .view-container {{
      width: 100%;
      height: 100%;
      display: flex;
      align-items: stretch;
      justify-content: stretch;
    }}
    .view-container > * {{
      flex: 1 1 auto;
      border: 0;
    }}
  </style>
</head>
<body>
  <div class="view-container">
    {inner_html}
  </div>
</body>
</html>"""

    return full_html

@app.route("/view_contact_3d")
def view_contact_3d_route():
    """
    Return an HTML page that embeds the interactive 3D viewer
    for a single contact at MNI (x, y, z).
    """
    x = request.args.get("x", default=30.0, type=float)
    y = request.args.get("y", default=-22.0, type=float)
    z = request.args.get("z", default=55.0, type=float)
    coord = [x, y, z]

    try:
        view = viewer.view_contact_3d(coord)
    except ValueError as e:
        return str(e), 400

    inner_html = view.get_iframe()

    full_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>3D contact view: ({x:.1f}, {y:.1f}, {z:.1f})</title>
  <style>
    html, body {{
      margin: 0;
      padding: 0;
      width: 100%;
      height: 100%;
      background: #000;
    }}
    .view-container {{
      width: 100%;
      height: 100%;
      display: flex;
      align-items: stretch;
      justify-content: stretch;
    }}
    .view-container > * {{
      flex: 1 1 auto;
      border: 0;
    }}
  </style>
</head>
<body>
  <div class="view-container">
    {inner_html}
  </div>
</body>
</html>"""
    return full_html

@app.route("/api/contact", methods=["POST"])
def api_contact():
    # Get form fields
    name = request.form.get("name", "")
    email = request.form.get("email", "")
    subject = request.form.get("subject", "(No subject)")
    message = request.form.get("message", "")

    # Build email body
    body = f"""New message from Tiantan NeuroDatabase website:

Name: {name}
Email: {email}
Subject: {subject}

Message:
{message}
"""

    # Email config
    TO_EMAIL = "hao.zhu.808@gmail.com"
    FROM_EMAIL = os.environ.get("CONTACT_FROM", TO_EMAIL)
    SMTP_USER = os.environ.get("CONTACT_SMTP_USER", TO_EMAIL)
    SMTP_PASS = os.environ.get("CONTACT_SMTP_PASS")  # Gmail app password
    SMTP_HOST = "smtp.gmail.com"
    SMTP_PORT = 587

    if not SMTP_PASS:
        return "Email not configured on server (CONTACT_SMTP_PASS missing).", 500

    # Build message
    msg = EmailMessage()
    msg["Subject"] = f"[Tiantan Website] {subject}"
    msg["From"] = FROM_EMAIL
    msg["To"] = TO_EMAIL
    if email:
        msg["Reply-To"] = email
    msg.set_content(body)

    # Send via Gmail SMTP
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
    except Exception as e:
        return f"Failed to send email: {e}", 500

    # Simple thank-you page
    return """
<!DOCTYPE html>
<html>
  <head><meta charset="utf-8"><title>Message sent</title></head>
  <body>
    <p>Thank you! Your message has been sent.</p>
    <p><a href="/contact.html">Back to contact page</a></p>
  </body>
</html>
"""

if __name__ == "__main__":
    # Run backend; adjust host/port as needed
    app.run(host="0.0.0.0", port=5200, debug=True)
