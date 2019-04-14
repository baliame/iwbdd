from .shader import Shader, Program
from OpenGL.GL import *
from OpenGL.arrays.vbo import VBO
from . import logger
import numpy as np


GSH_vtx = """
#version 430
layout(location = 0) in vec2 in_pos;
layout(location = 1) in vec2 in_uv;

layout(location = 0) out vec4 out_pos;
layout(location = 1) out vec2 out_uv;
layout(location = 2) out vec2 out_screen_uv;
layout(location = 3) out vec2 out_screen_pos;


uniform mat4 view;
uniform mat4 model;


void main() {
    out_pos = view * model * vec4(in_pos, 0, 1);
    out_uv = in_uv;
    out_screen_uv = vec2((out_pos.x + 1) / 2, (out_pos.y + 1) / 2);
    out_screen_pos = (model * vec4(in_pos, 0, 1)).xy;
    gl_Position = out_pos;
}

""".strip()

GSH_pix = """
#version 430

layout(binding = 0) uniform sampler2D sprite;
layout(binding = 1) uniform sampler2D screen;

layout(location = 1) in vec2 in_uv;
layout(location = 2) in vec2 in_screen_uv;

layout(location = 0) out vec4 out_color;

uniform vec4 colorize;

void main() {
    vec4 spr = texture(sprite, in_uv);
    vec4 scr = texture(screen, in_screen_uv);

    spr.a *= colorize.a;

    vec3 clr = spr.a * spr.rgb * colorize.rgb + (1 - spr.a) * scr.rgb;
    out_color = vec4(clr.rgb, 1);
}

""".strip()

GSH_pix_sheet = """
#version 430

layout(binding = 0) uniform sampler2DArray sprite;
layout(binding = 1) uniform sampler2D screen;

layout(location = 1) in vec2 in_uv;
layout(location = 2) in vec2 in_screen_uv;

layout(location = 0) out vec4 out_color;

uniform vec4 colorize;
uniform uint tex_idx;

void main() {
    vec4 spr = vec4(0, 0, 0, 0);
    if (tex_idx >= 0) {
        spr = texture(sprite, vec3(in_uv, float(tex_idx)));
    }
    vec4 scr = texture(screen, in_screen_uv);

    spr.a *= colorize.a;

    vec3 clr = spr.a * spr.rgb * colorize.rgb + (1 - spr.a) * scr.rgb;
    out_color = vec4(clr.rgb, 1);
}

""".strip()

GSH_pix_terrain = """
#version 430

layout(binding = 0) uniform sampler2DArray tileset;
layout(binding = 1) uniform sampler2D screen;
layout(binding = 2) uniform usampler2D tile_idx;

layout(location = 1) in vec2 in_uv;
layout(location = 2) in vec2 in_screen_uv;
layout(location = 3) in vec2 in_screen_pos;

layout(location = 0) out vec4 out_color;

uniform vec4 colorize;
uniform float tile_w, tile_h;

void main() {
    float tx = in_screen_pos.x / tile_w;
    uint tx_i = uint(tx);
    float ty = in_screen_pos.y / tile_h;
    uint ty_i = uint(ty);
    uvec4 tex_idxu = texelFetch(tile_idx, ivec2(int(in_screen_pos.x / tile_w), int(in_screen_pos.y / tile_h)), 0);
    float tex_idx = float(tex_idxu.r);

    vec4 spr = texture(tileset, vec3(tx - tx_i, ty - ty_i, tex_idx));
    vec4 scr = texture(screen, in_screen_uv);

    spr.a *= colorize.a;

    vec3 clr = spr.a * spr.rgb * colorize.rgb + (1 - spr.a) * scr.rgb;
    out_color = vec4(clr.rgb, 1);
}

""".strip()

GSH_pix_terrain_no_blend = """
#version 430

layout(binding = 0) uniform sampler2DArray tileset;
layout(binding = 1) uniform sampler2D screen;
layout(binding = 2) uniform usampler2D tile_idx;

layout(location = 1) in vec2 in_uv;
layout(location = 2) in vec2 in_screen_uv;
layout(location = 3) in vec2 in_screen_pos;

layout(location = 0) out vec4 out_color;

uniform float tile_w, tile_h;

void main() {
    float tx = in_screen_pos.x / tile_w;
    uint tx_i = uint(tx);
    float ty = in_screen_pos.y / tile_h;
    uint ty_i = uint(ty);
    uvec4 tex_idxu = texelFetch(tile_idx, ivec2(int(in_screen_pos.x / tile_w), int(in_screen_pos.y / tile_h)), 0);
    float tex_idx = float(tex_idxu.r);

    vec4 spr = texture(tileset, vec3(tx - tx_i, ty - ty_i, tex_idx));
    vec4 scr = texture(screen, in_screen_uv);

    if (spr.a > 0.5) {
        out_color = vec4(spr.rgb, 1);
    } else {
        out_color = vec4(scr.rgb, 1);
    }

}

""".strip()

GSH_blit = """
#version 430

layout(binding = 1) uniform sampler2D screen;

layout(location = 1) in vec2 in_uv;

layout(location = 0) out vec4 out_color;

uniform vec4 colorize;

void main() {
    vec4 blit_color = texture(screen, in_uv);
    out_color = vec4(blit_color.rgb * colorize.rgb, 1);
}
""".strip()

GSH_colorfill = """
#version 430

layout(location = 0) out vec4 out_color;

uniform vec4 colorize;

void main() {
    out_color = vec4(colorize.rgb, 1);
}
""".strip()

GSH_pix_hitboxgen = """
#version 430

layout(binding = 0) uniform sampler2DArray sprite;

layout(location = 1) in vec2 in_uv;

layout(location = 0) out vec4 out_color;

uniform vec4 colorize;
uniform float tex_idx;

void main() {
    vec4 spr = texture(sprite, vec3(in_uv, tex_idx));

    if (spr.a > 0.5) {
        out_color = vec4(colorize.rgb, 1);
    } else {
        out_color = vec4(0, 0, 0, 0);
    }
}

""".strip()

GSH_lens = """
#version 430

layout(binding = 1) uniform sampler2D screen;
layout(binding = 2) uniform sampler2D background;

layout(location = 1) in vec2 in_uv;
layout(location = 2) in vec2 in_screen_uv;

layout(location = 0) out vec4 out_color;

void main() {
    float ux = in_uv.x * 2 - 1;
    float sgnx = 1;
    if (ux < 0) {
        sgnx = -1;
    }
    float uy = in_uv.y * 2 - 1;
    float sgny = 1;
    if (uy < 0) {
        sgny = -1;
    }
    vec2 dist_uv = vec2(in_screen_uv.x + sgnx * (1 - ux * ux * ux * ux) * 0.02, in_screen_uv.y + sgny * (1 - uy * uy * uy * uy) * 0.03);
    vec4 scr = texture(screen, in_screen_uv);
    vec4 scr2 = texture(screen, dist_uv);
    vec4 bg = texture(background, dist_uv);
    float r2 = ux * ux + uy * uy;
    if (r2 > 1.05) {
        out_color = scr;
    }
    else if (r2 >= 0.95) {
        out_color = vec4(0, 0, 0, 1);
    }
    else {
        out_color = bg * 0.875 + scr * 0.125;
    }
}

""".strip()

GSH_lens_off = """
#version 430

layout(binding = 1) uniform sampler2D screen;
layout(binding = 2) uniform sampler2D background;

layout(location = 1) in vec2 in_uv;
layout(location = 2) in vec2 in_screen_uv;

layout(location = 0) out vec4 out_color;

void main() {
    vec4 scr = texture(screen, in_screen_uv);
    float ux = in_uv.x * 2 - 1;
    float uy = in_uv.y * 2 - 1;
    float r2 = ux * ux + uy * uy;
    if (r2 > 1.05) {
        out_color = scr;
    }
    else if (r2 >= 0.95) {
        out_color = vec4(0, 0, 0, 1);
    }
    else {
        out_color = scr;
    }
}

""".strip()

GSH_lens_coll = """
#version 430

layout(binding = 1) uniform sampler2D screen;
layout(binding = 2) uniform sampler2D background;

layout(location = 1) in vec2 in_uv;
layout(location = 2) in vec2 in_screen_uv;

layout(location = 0) out vec4 out_color;

void main() {
    vec4 scr = texture(screen, in_screen_uv);
    float ux = in_uv.x * 2 - 1;
    float uy = in_uv.y * 2 - 1;
    float r2 = ux * ux + uy * uy;
    if (r2 > 1.0) {
        out_color = scr;
    }
    else {
        out_color = vec4(0.5, 0, 0, 1.0);
    }
}

""".strip()

GSH_lens_semi = """
#version 430

layout(binding = 1) uniform sampler2D screen;
layout(binding = 2) uniform sampler2D background;

layout(location = 1) in vec2 in_uv;
layout(location = 2) in vec2 in_screen_uv;

layout(location = 0) out vec4 out_color;

void main() {
    vec4 scr = texture(screen, in_screen_uv);
    if (in_uv.y < 0.47) {
        out_color = scr;
    } else if (in_uv.y < 0.50) {
        out_color = vec4(0, 0, 0, 1);
    } else {
        float ux = in_uv.x * 2 - 1;
        float sgnx = 1;
        if (ux < 0) {
            sgnx = -1;
        }
        float uy = in_uv.y * 2 - 1;
        float sgny = 1;
        if (uy < 0) {
            sgny = -1;
        }
        vec2 dist_uv = vec2(in_screen_uv.x + sgnx * (1 - ux * ux * ux * ux) * 0.02, in_screen_uv.y + sgny * (1 - uy * uy * uy * uy) * 0.03);
        vec4 scr2 = texture(screen, dist_uv);
        vec4 bg = texture(background, dist_uv);
        float r2 = ux * ux + uy * uy;
        if (r2 > 1.05) {
            out_color = scr;
        }
        else if (r2 >= 0.95) {
            out_color = vec4(0, 0, 0, 1);
        }
        else {
            out_color = bg * 0.875 + scr * 0.125;
        }
    }
}

""".strip()

GSH_lens_semi_coll = """
#version 430

layout(binding = 1) uniform sampler2D screen;
layout(binding = 2) uniform sampler2D background;

layout(location = 1) in vec2 in_uv;
layout(location = 2) in vec2 in_screen_uv;

layout(location = 0) out vec4 out_color;

void main() {
    vec4 scr = texture(screen, in_screen_uv);
    if (in_uv.y < 0.48) {
        out_color = scr;
    } else {
        float ux = in_uv.x * 2 - 1;
        float uy = in_uv.y * 2 - 1;
        float r2 = ux * ux + uy * uy;
        if (r2 > 1.0) {
            out_color = scr;
        }
        else {
            out_color = vec4(0.5, 0, 0, 1.0);
        }
    }
}

""".strip()

GSH_fx_darkroom = """
#version 430

layout(binding = 1) uniform sampler2D screen;

uniform int   lightSourceOn[10];
uniform vec4  lightSourceColors[10];
uniform vec2  lightSourceLocs[10];
uniform float fullIntensityRadius;

layout(location = 2) in vec2 in_screen_uv;
layout(location = 3) in vec2 in_screen_pos;

layout(location = 0) out vec4 out_color;

void main() {
    vec4 scr = texture(screen, in_screen_uv);
    scr.a = 0;

    for (int i = 0; i < 10; i++) {
        if (lightSourceOn[i] != 0) {
            float dx = in_screen_pos.x - lightSourceLocs[i].x;
            float dy = in_screen_pos.y - lightSourceLocs[i].y;
            float r2 = dx * dx + dy * dy;
            float r = sqrt(r2);
            float rm = lightSourceColors[i].a;
            float rf = fullIntensityRadius * rm;
            float rv = rf - r;
            float ra = rv / rf * 0.5;
            if (rv >= 0) {
                scr.rgb = lightSourceColors[i].rgb * ra + scr.rgb * (1 - ra);
                scr.a = ra + scr.a * (1 - ra);
            }
        }
    }
    out_color = vec4(scr.rgb * scr.a, 1);
}

""".strip()


GSH_fx_hsv_rotate = """
#version 430

layout(binding = 1) uniform sampler2D screen;

uniform int t;

layout(location = 2) in vec2 in_screen_uv;

layout(location = 0) out vec4 out_color;

void main() {
    vec4 scr = texture(screen, in_screen_uv);
    float h = 0;
    float s = 0;
    float v = 0;
    if (scr.r > scr.g && scr.r > scr.b) {
        h = 60 * (scr.g - scr.b) / (scr.r - min(scr.g, scr.b));
        s = (scr.r - min(scr.g, scr.b)) / scr.r;
        v = scr.r;
    } else if (scr.g > scr.r && scr.g > scr.b) {
        h = 60 * (2 + (scr.b - scr.r) / (scr.g - min(scr.r, scr.b)));
        s = (scr.g - min(scr.r, scr.b)) / scr.g;
        v = scr.g;
    } else if (scr.b > scr.r && scr.b > scr.g) {
        h = 60 * (4 + (scr.r - scr.g) / (scr.b - min(scr.r, scr.g)));
        s = (scr.b - min(scr.r, scr.g)) / scr.b;
        v = scr.b;
    }
    h += t;
    while (h < 0) {
        h += 360;
    }
    while (h >= 360) {
        h -= 360;
    }
    float C = s * v;
    float H2 = h / 60;
    float X = C * (1 - abs(mod(H2, 2) - 1));
    vec3 res = vec3(0, 0, 0);
    if (H2 >= 0 && H2 <= 1) {
        res = vec3(C, X, 0);
    } else if (H2 >= 1 && H2 <= 2) {
        res = vec3(X, C, 0);
    } else if (H2 >= 2 && H2 <= 3) {
        res = vec3(0, C, X);
    } else if (H2 >= 3 && H2 <= 4) {
        res = vec3(0, X, C);
    } else if (H2 >= 4 && H2 <= 5) {
        res = vec3(X, 0, C);
    } else if (H2 >= 5 && H2 <= 6) {
        res = vec3(C, 0, X);
    }
    float m = v - C;
    out_color = vec4(res.r + m, res.g + m, res.b + m, 1);
}

""".strip()

GSH_fx_vertical_sine = """
#version 430

layout(binding = 1) uniform sampler2D screen;

uniform int t;

layout(location = 2) in vec2 in_screen_uv;
layout(location = 3) in vec2 in_screen_pos;


layout(location = 0) out vec4 out_color;

void main() {
    float yrad = (in_screen_pos.y + t) / 180 * 3.141592;
    vec2 distortion = vec2(sin(yrad) * 0.05, 0);
    out_color = texture(screen, in_screen_uv + distortion);
}
""".strip()


_GSH_all = [
    (GL_VERTEX_SHADER, "GSH_vtx"),
    (GL_FRAGMENT_SHADER, "GSH_pix"),
    (GL_FRAGMENT_SHADER, "GSH_pix_sheet"),
    (GL_FRAGMENT_SHADER, "GSH_pix_terrain"),
    (GL_FRAGMENT_SHADER, "GSH_blit"),
    (GL_FRAGMENT_SHADER, "GSH_pix_terrain_no_blend"),
    (GL_FRAGMENT_SHADER, "GSH_colorfill"),
    (GL_FRAGMENT_SHADER, "GSH_pix_hitboxgen"),
    (GL_FRAGMENT_SHADER, "GSH_lens"),
    (GL_FRAGMENT_SHADER, "GSH_lens_off"),
    (GL_FRAGMENT_SHADER, "GSH_lens_coll"),
    (GL_FRAGMENT_SHADER, "GSH_lens_semi"),
    (GL_FRAGMENT_SHADER, "GSH_lens_semi_coll"),
    (GL_FRAGMENT_SHADER, "GSH_fx_darkroom"),
    (GL_FRAGMENT_SHADER, "GSH_fx_hsv_rotate"),
    (GL_FRAGMENT_SHADER, "GSH_fx_vertical_sine"),
]
_GSH_progs = {
    "GSHP_render": {GL_VERTEX_SHADER: "GSH_vtx", GL_FRAGMENT_SHADER: "GSH_pix"},
    "GSHP_render_sheet": {GL_VERTEX_SHADER: "GSH_vtx", GL_FRAGMENT_SHADER: "GSH_pix_sheet"},
    "GSHP_render_terrain": {GL_VERTEX_SHADER: "GSH_vtx", GL_FRAGMENT_SHADER: "GSH_pix_terrain"},
    "GSHP_render_terrain_no_blend": {GL_VERTEX_SHADER: "GSH_vtx", GL_FRAGMENT_SHADER: "GSH_pix_terrain_no_blend"},
    "GSHP_blit": {GL_VERTEX_SHADER: "GSH_vtx", GL_FRAGMENT_SHADER: "GSH_blit"},
    "GSHP_colorfill": {GL_VERTEX_SHADER: "GSH_vtx", GL_FRAGMENT_SHADER: "GSH_colorfill"},
    "GSHP_hitboxgen": {GL_VERTEX_SHADER: "GSH_vtx", GL_FRAGMENT_SHADER: "GSH_pix_hitboxgen"},
    "GSHP_lens": {GL_VERTEX_SHADER: "GSH_vtx", GL_FRAGMENT_SHADER: "GSH_lens"},
    "GSHP_lens_off": {GL_VERTEX_SHADER: "GSH_vtx", GL_FRAGMENT_SHADER: "GSH_lens_off"},
    "GSHP_lens_coll": {GL_VERTEX_SHADER: "GSH_vtx", GL_FRAGMENT_SHADER: "GSH_lens_coll"},
    "GSHP_lens_semi": {GL_VERTEX_SHADER: "GSH_vtx", GL_FRAGMENT_SHADER: "GSH_lens_semi"},
    "GSHP_lens_semi_coll": {GL_VERTEX_SHADER: "GSH_vtx", GL_FRAGMENT_SHADER: "GSH_lens_semi_coll"},
    "GSHP_fx_darkroom": {GL_VERTEX_SHADER: "GSH_vtx", GL_FRAGMENT_SHADER: "GSH_fx_darkroom"},
    "GSHP_fx_hsv_rotate": {GL_VERTEX_SHADER: "GSH_vtx", GL_FRAGMENT_SHADER: "GSH_fx_hsv_rotate"},
    "GSHP_fx_vertical_sine": {GL_VERTEX_SHADER: "GSH_vtx", GL_FRAGMENT_SHADER: "GSH_fx_vertical_sine"},
}
GSH_compiled = {}
GSH_programs = {}
GSH_wasinit = False
GSH_vaos = {}


def GSH_init():
    global _GSH_all, _GSH_progs, GSH_compiled, GSH_programs, GSH_wasinit, GSH_vaos
    if GSH_wasinit:
        return
    g = globals()
    for v in _GSH_all:
        s = Shader(v[0], g[v[1]])
        GSH_compiled[v[1]] = s
    for prog, spec in _GSH_progs.items():
        p = Program()
        for t, s in spec.items():
            p.attach(GSH_compiled[s])
        p.link()
        GSH_programs[prog] = p
    GSH_vaos['unit'] = glGenVertexArrays(1)
    glBindVertexArray(GSH_vaos['unit'])
    vbo = VBO(np.array([0, 0, 1, 0, 0, 1, 1, 1], dtype='f'))
    vbo.bind()
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, vbo)
    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 0, vbo)
    vbo.unbind()
    glEnableVertexAttribArray(0)
    glEnableVertexAttribArray(1)
    glBindVertexArray(0)
    GSH_wasinit = True


def GSH(prog):
    p = GSH_programs[prog]
    if p is None:
        raise RuntimeError("cannot find the program {0}".format(prog))
    p.persistent = False
    return p


def GSHp(prog):
    p = GSH_programs[prog]
    if p is None:
        raise RuntimeError("cannot find the program {0}".format(prog))
    p.persistent = True
    return p
