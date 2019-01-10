vtx = """
#version 430
layout(location = 0) in vec2 in_pos;

out vec4 out_pos;

uniform mat4 view;
uniform mat4 model;

void main() {
	out_pos = view * model * vec4(in_pos, 0, 1);
}

""".strip()