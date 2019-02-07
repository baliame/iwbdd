from .shader import Shader, Program
from OpenGL.GL import *
from . import logger

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

    vec3 clr = spr.a * spr.rgb + (1 - spr.a) * scr.rgb;
    out_color = vec4(clr.rgb * colorize.rgb, 1);
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

    vec3 clr = spr.a * spr.rgb + (1 - spr.a) * scr.rgb;
    out_color = vec4(clr.rgb * colorize.rgb, 1);
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
    // out_color = vec4(in_screen_pos.x / (tile_w * 42), in_screen_pos.y / (tile_h * 32), 0, 1);
    // return;

    // float tex_idx = float(texelFetch(tile_idx, ivec2(41, 31), 0).r);
    float tx = in_screen_pos.x / tile_w;
    uint tx_i = uint(tx);
    float ty = in_screen_pos.y / tile_h;
    uint ty_i = uint(ty);
    uvec4 tex_idxu = texelFetch(tile_idx, ivec2(int(in_screen_pos.x / tile_w), int(in_screen_pos.y / tile_h)), 0);
    float tex_idx = float(tex_idxu.r);
    // float tex_idx = texture(tile_idx, vec2(in_screen_pos.x / tile_w, in_screen_pos.y / tile_h)).r;

    // out_color = vec4(vec3(tex_idxu.rgb), 1);
    // return;

    vec4 spr = texture(tileset, vec3(tx - tx_i, ty - ty_i, tex_idx));
    vec4 scr = texture(screen, in_screen_uv);

    spr.a *= colorize.a;

    vec3 clr = spr.a * spr.rgb + (1 - spr.a) * scr.rgb;
    // vec3 clr = 0.5 * spr.rgb + 0.5 * scr.rgb;
    out_color = vec4(clr.rgb * colorize.rgb, 1);
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

_GSH_all = [(GL_VERTEX_SHADER, "GSH_vtx"), (GL_FRAGMENT_SHADER, "GSH_pix"), (GL_FRAGMENT_SHADER, "GSH_pix_sheet"), (GL_FRAGMENT_SHADER, "GSH_pix_terrain"), (GL_FRAGMENT_SHADER, "GSH_blit")]
_GSH_progs = {"GSHP_render": {GL_VERTEX_SHADER: "GSH_vtx", GL_FRAGMENT_SHADER: "GSH_pix"}, "GSHP_render_sheet": {GL_VERTEX_SHADER: "GSH_vtx", GL_FRAGMENT_SHADER: "GSH_pix_sheet"}, "GSHP_render_terrain": {GL_VERTEX_SHADER: "GSH_vtx", GL_FRAGMENT_SHADER: "GSH_pix_terrain"}, "GSHP_blit": {GL_VERTEX_SHADER: "GSH_vtx", GL_FRAGMENT_SHADER: "GSH_blit"}}
GSH_compiled = {}
GSH_programs = {}
GSH_wasinit = False


def GSH_init():
    global _GSH_all, _GSH_progs, GSH_compiled, GSH_programs, GSH_wasinit
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
