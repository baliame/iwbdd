enable_log = False
log_fb_bound = None


def log_draw():
    if not enable_log:
        return
    print('DRAW: did draw with {0}'.format('no bound framebuffer' if log_fb_bound is None else 'framebuffer named "{0}"'.format(log_fb_bound)))


def log_read_copy(fbo_name):
    if not enable_log:
        return
    print('PASS: new render pass, copied transparency in framebuffer named "{0}"'.format(fbo_name))


def log_uniform(name, value, typename):
    if not enable_log:
        return
    print('UNIFORM: assigning {2} {0} = {1}'.format(name, value, typename))
