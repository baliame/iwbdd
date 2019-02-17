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
uniform float tex_idx;

void main() {
    vec4 spr = texture(sprite, vec3(in_uv, tex_idx));
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
        out_color = bg * 0.75 + scr * 0.25;
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
            out_color = bg * 0.75 + scr * 0.25;
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
