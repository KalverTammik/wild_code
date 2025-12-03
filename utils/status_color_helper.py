class StatusColorHelper:
    """
    Helper class for color and contrast calculations for status chips.
    Provides static methods for color conversion, contrast, and status chip color selection.
    """
    @staticmethod
    def clamp(x, a, b):
        return max(a, min(b, x))

    @staticmethod
    def hex_to_rgb(hexstr):
        s = hexstr.strip().lstrip('#')
        if len(s) == 3:
            s = ''.join([c*2 for c in s])
        try:
            return tuple(int(s[i:i+2], 16) for i in (0, 2, 4))
        except Exception:
            return (204, 204, 204)

    @staticmethod
    def rgb_to_hsl(r, g, b):
        r, g, b = [v/255.0 for v in (r, g, b)]
        mx, mn = max(r, g, b), min(r, g, b)
        l = (mx + mn) / 2.0
        if mx == mn:
            return 0.0, 0.0, l
        d = mx - mn
        s = d / (2.0 - mx - mn) if l > 0.5 else d / (mx + mn)
        if mx == r:
            h = ((g - b) / d + (6 if g < b else 0)) % 6
        elif mx == g:
            h = (b - r) / d + 2
        else:
            h = (r - g) / d + 4
        h *= 60
        return h, s, l

    @staticmethod
    def hsl_to_rgb(h, s, l):
        c = (1 - abs(2*l - 1)) * s
        x = c * (1 - abs(((h/60.0) % 2) - 1))
        m = l - c/2
        if   0 <= h < 60:   rp, gp, bp = c, x, 0
        elif 60 <= h < 120: rp, gp, bp = x, c, 0
        elif 120 <= h < 180:rp, gp, bp = 0, c, x
        elif 180 <= h < 240:rp, gp, bp = 0, x, c
        elif 240 <= h < 300:rp, gp, bp = x, 0, c
        else:               rp, gp, bp = c, 0, x
        r, g, b = [(v + m) * 255 for v in (rp, gp, bp)]
        return int(round(r)), int(round(g)), int(round(b))

    @staticmethod
    def rel_luminance(r, g, b):
        def f(c):
            c = c/255.0
            return c/12.92 if c <= 0.04045 else ((c+0.055)/1.055) ** 2.4
        R, G, B = f(r), f(g), f(b)
        return 0.2126*R + 0.7152*G + 0.0722*B

    @staticmethod
    def contrast_ratio(rgb1, rgb2):
        L1 = StatusColorHelper.rel_luminance(*rgb1)
        L2 = StatusColorHelper.rel_luminance(*rgb2)
        L1, L2 = max(L1, L2), min(L1, L2)
        return (L1 + 0.05) / (L2 + 0.05)

    @staticmethod
    def _get_text_color_for_background(rgb):
        """Return a soft light/dark/tinted tuple based on perceived brightness."""
        r, g, b = rgb
        brightness = (r * 299 + g * 587 + b * 114) / 1000

        # Hue-based override: treat orange as needing light text
        h, s, _ = StatusColorHelper.rgb_to_hsl(r, g, b)
        # h is 0–1 → orange-ish ≈ 15–45 degrees
        if 0.04 <= h <= 0.12 and brightness > 130:
            return (242, 242, 252)  # soft off-white

        if brightness < 130:
            return (242, 242, 252)  # light on dark
        if brightness < 210:
            return (34, 36, 48)     # dark on mid
        return StatusColorHelper._tinted_dark_for_bright(rgb)


    @staticmethod
    def _tinted_dark_for_bright(rgb):
        h, s, _ = StatusColorHelper.rgb_to_hsl(*rgb)
        s = StatusColorHelper.clamp(s, 0.40, 0.85)
        l = 0.25
        return StatusColorHelper.hsl_to_rgb(h, s * 0.8, l)

    @staticmethod
    def upgrade_status_color(hex_color):
        """Take possibly pastel hex, return tuned (bg_rgb, fg_rgb, border_rgb)."""
        r, g, b = StatusColorHelper.hex_to_rgb(hex_color)

        h, s, l = StatusColorHelper.rgb_to_hsl(r, g, b)

        # Optional: special treatment for orange-ish hues
        if 20 <= h <= 55:
            s = StatusColorHelper.clamp(s, 0.55, 0.9)   # nicely saturated orange
            l = StatusColorHelper.clamp(l, 0.45, 0.62)  # not too pale, not too dark

        # General normalization to "chip-friendly" range
        s = max(s, 0.35)
        l = StatusColorHelper.clamp(l, 0.35, 0.65)

        r, g, b = StatusColorHelper.hsl_to_rgb(h, s, l)
        bg = (r, g, b)

        white, black = (255, 255, 255), (0, 0, 0)
        cr_white = StatusColorHelper.contrast_ratio(bg, white)
        cr_black = StatusColorHelper.contrast_ratio(bg, black)

        target = 4.5
        if max(cr_white, cr_black) < target:
            if cr_white > cr_black:
                h, s, l = StatusColorHelper.rgb_to_hsl(*bg)
                l = StatusColorHelper.clamp(l - 0.06, 0.28, 0.72)
                bg = StatusColorHelper.hsl_to_rgb(h, s, l)
            else:
                h, s, l = StatusColorHelper.rgb_to_hsl(*bg)
                l = StatusColorHelper.clamp(l + 0.06, 0.28, 0.72)
                bg = StatusColorHelper.hsl_to_rgb(h, s, l)

            cr_white = StatusColorHelper.contrast_ratio(bg, white)
            cr_black = StatusColorHelper.contrast_ratio(bg, black)

        fg = StatusColorHelper._get_text_color_for_background(bg)

        h, s, l = StatusColorHelper.rgb_to_hsl(*bg)
        if l >= 0.5:
            border_l = StatusColorHelper.clamp(l - 0.12, 0.15, 0.85)
        else:
            border_l = StatusColorHelper.clamp(l + 0.12, 0.15, 0.85)
        border = StatusColorHelper.hsl_to_rgb(h, s, border_l)

        return bg, fg, border
