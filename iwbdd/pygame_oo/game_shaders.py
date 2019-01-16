from .shader import Shader, Program
from OpenGL.GL import *

GSH_vtx = """
#version 430
layout(location = 0) in vec2 in_pos;
layout(location = 1) in vec2 in_uv;

layout(location = 0) out vec4 out_pos;
layout(location = 1) out vec2 out_uv;
layout(location = 2) out vec2 out_screen_uv;

uniform mat4 view;
uniform mat4 model;

void main() {
    out_pos = view * model * vec4(in_pos, 0, 1);
    out_uv = in_uv;
    out_screen_uv = out_pos.xy;
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

    vec3 clr = spr.a * spr.rgb + (1 - spr.a) * scr.rgb;
    out_color = vec4(clr.rgb, 1);
}

""".strip()

GSH_blit = """
#version 430

layout(binding = 1) uniform sampler2D screen;

layout(location = 1) in vec2 in_uv;
layout(location = 2) in vec2 in_screen_uv;

layout(location = 0) out vec4 out_color;

void main() {
    out_color = texture(screen, in_uv);
}
""".strip()

_GSH_all = [(GL_VERTEX_SHADER, "GSH_vtx"), (GL_FRAGMENT_SHADER, "GSH_pix"), (GL_FRAGMENT_SHADER, "GSH_pix_sheet"), (GL_FRAGMENT_SHADER, "GSH_blit")]
_GSH_progs = {"GSHP_render": {GL_VERTEX_SHADER: "GSH_vtx", GL_FRAGMENT_SHADER: "GSH_pix"}, "GSHP_render_sheet": {GL_VERTEX_SHADER: "GSH_vtx", GL_FRAGMENT_SHADER: "GSH_pix_sheet"}, "GSHP_blit": {GL_VERTEX_SHADER: "GSH_vtx", GL_FRAGMENT_SHADER: "GSH_blit"}}
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
            p.attach(s)
        p.link()
        GSH_programs[prog] = p
    GSH_wasinit = True


def GSH(prog):
    return GSH_programs[prog]