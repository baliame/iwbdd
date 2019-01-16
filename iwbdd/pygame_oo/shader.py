from OpenGL.GL import *


class Shader:
    def __init__(self, shader_type, code):
        self.shader = glCreateShader(shader_type)
        try:
            glShaderSource(self.shader, code)
            glCompileShader(self.shader)
            if glGetShaderiv(self.shader, GL_COMPILE_STATUS) != GL_TRUE:
                info = glGetShaderInfoLog(self.shader)
                raise RuntimeError('Failed to compile shader: %s' % info)
        except:
            glDeleteShader(self.shader)
            raise


class Program:
    def __init__(self):
        self.prog = glCreateProgram()
        self.linked = False

    def attach(self, shader):
        if linked:
            raise RuntimeError('Cannot attach shaders to linked program.')
        glAttachShader(self.prog, shader.shader)

    def link(self):
        glLinkProgram(self.prog)
        if glGetProgramiv(self.prog, GL_LINK_STATUS) != GL_TRUE:
            info = glGetProgramInfoLog(self.prog)
            raise RuntimeError('Failed to link program: %s' % info)
        self.linked = True

    def use(self):
        if not self.linked:
            raise RuntimeError('Program must be linked before use.')
        glUseProgram(self.prog)

    def __enter__(self):
        self.use()

    def __exit__(self, type, value, traceback):
        glUseProgram(None)
