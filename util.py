from pygame.font import SysFont

font = None


def draw_text(surface, color, text, position, size, anchor=''):
    global font
    # if font is None or size > 256:
    font = SysFont('consolas', size * 3 // 4)
    textobj = font.render(text, 1, color)
    textrect = textobj.get_rect()
    if anchor == 'bottomleft':
        textrect.bottomleft = position
    elif anchor == 'topleft':
        textrect.topleft = position
    elif anchor == 'bottomright':
        textrect.bottomright = position
    elif anchor == 'topright':
        textrect.topright = position
    else:
        textrect.center = position
    surface.blit(textobj, textrect)
    return textrect

def clamp(a, b, c):
    if a < b:
        return b
    if a > c:
        return c
    return a