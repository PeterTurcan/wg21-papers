"""Logo loading for raster and SVG images."""


def load_logo(path, height):
    """Load a logo image (SVG or raster) and return a ReportLab flowable."""
    from reportlab.platypus import Image as RLImage
    path = str(path)
    if path.lower().endswith(".svg"):
        from svglib.svglib import svg2rlg
        drawing = svg2rlg(path)
        if drawing is None:
            return None
        scale = height / drawing.height
        drawing.width *= scale
        drawing.height = height
        drawing.scale(scale, scale)
        return drawing
    return RLImage(path, height=height, kind="proportional")
