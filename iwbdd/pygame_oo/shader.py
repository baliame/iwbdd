from OpenGL.GL import *
import numpy as np
from math import sin, cos
from . import logger


class Shader:
    def __init__(self, shader_type, code):
        self.shader = glCreateShader(shader_type)
        try:
            glShaderSource(self.shader, code)
            glCompileShader(self.shader)
            if glGetShaderiv(self.shader, GL_COMPILE_STATUS) != GL_TRUE:
                info = glGetShaderInfoLog(self.shader)
                raise RuntimeError('Failed to compile shader:\n{0}\n\nCODE:\n{1}'.format(info.decode('utf-8'), code))
        except:
            glDeleteShader(self.shader)
            raise


class Program:
    last_use = None

    def __init__(self):
        self.prog = glCreateProgram()
        self.linked = False
        self.persistent = False
        self.uniform_locs = {}

    def attach(self, shader):
        if self.linked:
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
        if value is None:
            raise RuntimeError('Cannot assign None as value to uniform {0}'.format(name))
        try:
            value.uniform(loc, name)
        except AttributeError as e:
            if isinstance(value, float):
                logger.log_uniform(name, value, 'float')
                glUniform1f(loc, value)
            elif isinstance(value, int):
                if unsigned:
                    logger.log_uniform(name, value, 'unsigned int')
                    glUniform1ui(loc, value)
                else:
                    logger.log_uniform(name, value, 'int')
                    glUniform1i(loc, value)
            else:
                raise ValueError('Cannot deduce uniform type, call glUniform directly. (Original AttributeError: {0})'.format(e))

    def uniform_loc(self, name):
        try:
            return self.uniform_locs[name]
        except KeyError:
            self.uniform_locs[name] = glGetUniformLocation(self.prog, name)
            return self.uniform_locs[name]

    def __enter__(self):
        if not (self.persistent and Program.last_use == self):
            self.use()
        return self

    def __exit__(self, type, value, traceback):
        if not self.persistent:
            glUseProgram(0)


class IntArray:
    def __init__(self, vals, unsigned=False):
        self.vals = np.array(vals, dtype=np.int32 if not unsigned else np.uint32)
        self.unsigned = unsigned

    def uniform(self, loc, name):
        if self.unsigned:
            logger.log_uniform(name, self.vals, 'unsigned array (x{0})'.format(len(self.vals)))
            glUniform1uiv(loc, len(self.vals), self.vals)
        else:
            logger.log_uniform(name, self.vals, 'int array (x{0})'.format(len(self.vals)))
            glUniform1iv(loc, len(self.vals), self.vals)


class Vec2:
    def __init__(self, x=0, y=0, dtype='f'):
        self.data = np.array([x, y], dtype='f')
        self.dtype = dtype

    def __add__(self, v):
        return Vec2(self.data[0] + v.data[0], self.data[1] + v.data[1], self.dtype)

    def __iadd__(self, v):
        self.data = np.array([self.data[0] + v.data[0], self.data[1] + v.data[1]], dtype=self.dtype)
        return self

    def __mul__(self, v):
        return self.data[0] * v.data[0] + self.data[1] * v.data[1]

    def uniform(self, loc, name):
        if self.dtype == 'f' or self.dtype == float or self.dtype == np.float:
            logger.log_uniform(name, self.data, 'float vector (2)')
            glUniform2fv(loc, 1, self.data)
        elif self.dtype == 'U' or self.dtype == np.uint32:
            logger.log_uniform(name, self.data, 'unsigned vector (2)')
            glUniform2uiv(loc, 1, self.data)
        elif self.dtype == 'I' or self.dtype == np.int32:
            logger.log_uniform(name, self.data, 'int vector (2)')
            glUniform2iv(loc, 1, self.data)


class Vec2Array:
    def __init__(self, vecs, dtype='f'):
        self.vecs = np.array([(d.data[0], d.data[1]) for d in vecs], dtype=dtype)
        self.dtype = dtype

    def uniform(self, loc, name):
        if self.dtype == 'f' or self.dtype == float or self.dtype == np.float:
            logger.log_uniform(name, self.vecs, 'float vector (2) array (x{0})'.format(len(self.vecs)))
            glUniform2fv(loc, len(self.vecs), self.vecs)
        elif self.dtype == 'U' or self.dtype == np.uint32:
            logger.log_uniform(name, self.vecs, 'unsigned vector (2) array (x{0})'.format(len(self.vecs)))
            glUniform2uiv(loc, len(self.vecs), self.vecs)
        elif self.dtype == 'I' or self.dtype == np.int32:
            logger.log_uniform(name, self.vecs, 'int vector (2) array (x{0})'.format(len(self.vecs)))
            glUniform2iv(loc, len(self.vecs), self.vecs)


class Vec4:
    def __init__(self, x=0, y=0, z=0, w=1, dtype='f'):
        self.data = np.array([x, y, z, w], dtype='f')
        self.dtype = dtype

    def __add__(self, v):
        return Vec4(self.data[0] + v.data[0], self.data[1] + v.data[1], self.data[2] + v.data[2], self.data[3] + v.data[3], self.dtype)

    def __iadd__(self, v):
        self.data = np.array([self.data[0] + v.data[0], self.data[1] + v.data[1], self.data[2] + v.data[2], self.data[3] + v.data[3]], dtype=self.dtype)
        return self

    def __mul__(self, v):
        return Vec4(self.data[0] * v.data[0], self.data[1] * v.data[1], self.data[2] * v.data[2], self.data[3] * v.data[3], self.dtype)

    def __imul__(self, v):
        self.data = np.array([self.data[0] * v.data[0], self.data[1] * v.data[1], self.data[2] * v.data[2], self.data[3] * v.data[3]], dtype=self.dtype)
        return self

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

    def uniform(self, loc, name):
        if self.dtype == 'f' or self.dtype == float or self.dtype == np.float:
            logger.log_uniform(name, self.data, 'float vector')
            glUniform4fv(loc, 1, self.data)
        elif self.dtype == 'U' or self.dtype == np.uint32:
            logger.log_uniform(name, self.data, 'unsigned vector')
            glUniform4uiv(loc, 1, self.data)
        elif self.dtype == 'I' or self.dtype == np.int32:
            logger.log_uniform(name, self.data, 'int vector')
            glUniform4iv(loc, 1, self.data)


class Vec4Array:
    def __init__(self, vecs, dtype='f'):
        self.vecs = np.array([(d.data[0], d.data[1], d.data[2], d.data[3]) for d in vecs], dtype=dtype)
        self.dtype = dtype

    def uniform(self, loc, name):
        if self.dtype == 'f' or self.dtype == float or self.dtype == np.float:
            logger.log_uniform(name, self.vecs, 'float vector (4) array (x{0})'.format(len(self.vecs)))
            glUniform4fv(loc, len(self.vecs), self.vecs)
        elif self.dtype == 'U' or self.dtype == np.uint32:
            logger.log_uniform(name, self.vecs, 'unsigned vector (4) array (x{0})'.format(len(self.vecs)))
            glUniform4uiv(loc, len(self.vecs), self.vecs)
        elif self.dtype == 'I' or self.dtype == np.int32:
            logger.log_uniform(name, self.vecs, 'int vector (4) array (x{0})'.format(len(self.vecs)))
            glUniform4iv(loc, len(self.vecs), self.vecs)


class Mat4:
    def __init__(self):
        self.data = np.identity(4)

    @classmethod
    def translation(cls, x=0, y=0, z=0):
        ret = cls()
        # ret.data[0, 3] = x
        # ret.data[1, 3] = y
        # ret.data[2, 3] = z
        ret.data[3, 0] = x
        ret.data[3, 1] = y
        ret.data[3, 2] = z
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
        return self

    def translate(self, x=0, y=0, z=0):
        self *= self.__class__.translation(x, y, z)
        return self

    def rotate(self, angle=0):
        self *= self.__class__.rotation(angle)
        return self

    def scale(self, x=1, y=1, z=1):
        self *= self.__class__.scaling(x, y, z)
        return self

    def uniform(self, loc, name):
        logger.log_uniform(name, self.data, '4x4 float matrix')
        glUniformMatrix4fv(loc, 1, False, self.data)
