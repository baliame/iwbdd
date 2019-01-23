from OpenGL.GL import *
import numpy as np
from math import sin, cos


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
    last_use = None

    def __init__(self):
        self.prog = glCreateProgram()
        self.linked = False
        self.persistent = False

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
        if self.persistent:
            Program.last_use = self
        else:
            Program.last_use = None

    def uniform(self, name, value, unsigned=False):
        loc = self.uniform_loc(name)
        try:
            value.uniform(loc)
        except AttributeError as e:
            if isinstance(value, float):
                glUniform1f(loc, value)
            elif isinstance(value, int):
                if unsigned:
                    glUniform1ui(loc, value)
                else:
                    glUniform1i(loc, value)
            else:
                raise ValueError('Cannot deduce uniform type, call glUniform directly.')

    def uniform_loc(self, name):
        return glGetUniformLocation(self.prog, name)

    def __enter__(self):
        if not (self.persistent and Program.last_use == self):
            self.use()

    def __exit__(self, type, value, traceback):
        if not self.persistent:
            glUseProgram(None)


class Vec4:
    def __init__(self, x=0, y=0, z=0, w=1, dtype='f'):
        self.data = np.array([x, y, z, w], dtype='f')
        self.dtype = dtype

    def __add__(self, v):
        return Vec4(self.data[0] + v.data[0], self.data[1] + v.data[1], self.data[2] + v.data[2], self.data[3] + v.data[3], self.dtype)

    def __iadd__(self, v):
        self.data = np.array([self.data[0] + v.data[0], self.data[1] + v.data[1], self.data[2] + v.data[2], self.data[3] + v.data[3]], dtype=self.dtype)

    def __mul__(self, v):
        return Vec4(self.data[0] * v.data[0], self.data[1] * v.data[1], self.data[2] * v.data[2], self.data[3] * v.data[3], self.dtype)

    def __imul__(self, v):
        self.data = np.array([self.data[0] * v.data[0], self.data[1] * v.data[1], self.data[2] * v.data[2], self.data[3] * v.data[3]], dtype=self.dtype)

    def load_rgb(self, i):
        if i is None:
            r = 1.0
            g = 1.0
            b = 1.0
        else:
            r = (i & 0xFF0000) / float(0xFF0000)
            g = (i & 0x00FF00) / float(0x00FF00)
            b = (i & 0x0000FF) / float(0x0000FF)
        self.data[0] = r
        self.data[1] = g
        self.data[2] = b
        self.data[3] = 1.0

    def load_rgb_a(self, i, a):
        if i is None:
            r = 1.0
            g = 1.0
            b = 1.0
        else:
            r = (i & 0xFF0000) / float(0xFF0000)
            g = (i & 0x00FF00) / float(0x00FF00)
            b = (i & 0x0000FF) / float(0x0000FF)
        self.data[0] = r
        self.data[1] = g
        self.data[2] = b
        self.data[3] = a / 255.0

    def load_rgba(self, i):
        if i is None:
            r = 1.0
            g = 1.0
            b = 1.0
            a = 1.0
        else:
            r = (i & 0xFF000000) / float(0xFF000000)
            g = (i & 0x00FF0000) / float(0x00FF0000)
            b = (i & 0x0000FF00) / float(0x0000FF00)
            a = (i & 0x000000FF) / float(0x000000FF)
        self.data[0] = r
        self.data[1] = g
        self.data[2] = b
        self.data[3] = a

    def uniform(self, loc):
        if self.dtype == 'f' or self.dtype == float:
            glUniform4fv(loc, self.data)
        elif self.dtype == 'U':
            glUniform4uiv(loc, self.data)
        elif self.dtype == 'I':
            glUniform4uiv(loc, self.data)


class Mat4:
    def __init__(self):
        self.data = np.identity(4)

    @classmethod
    def translation(cls, x=0, y=0, z=0):
        ret = cls()
        ret.data[0, 3] = x
        ret.data[1, 3] = y
        ret.data[2, 3] = z
        return ret

    @classmethod
    def scaling(cls, x=1, y=1, z=1):
        ret = cls()
        ret.data[0, 0] = x
        ret.data[1, 1] = y
        ret.data[2, 2] = z
        return ret

    @classmethod
    def rotation(cls, angle=0):
        ret = cls()
        sa = sin(angle)
        ca = cos(angle)
        ret.data[0, 0] = ca
        ret.data[0, 1] = -sa
        ret.data[1, 0] = sa
        ret.data[1, 1] = ca
        return ret

    def __mul__(self, o):
        dest = self.__class__()
        dest.data = np.matmul(self.data, o.data)
        return dest

    def __imul__(self, o):
        self.data = np.matmul(self.data, o.data)
        return dest

    def translate(self, x=0, y=0, z=0):
        self *= self.__class__.translation(x, y, z)

    def rotate(self, angle=0):
        self *= self.__class__.rotation(angle)

    def scale(self, x=1, y=1, z=1):
        self *= self.__class__.scaling(x, y, z)

    def uniform(self, loc):
        glUniformMatrix4fv(loc, 1, False, self.data)
