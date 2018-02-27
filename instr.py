class Instr(object):
  def apply(self, pe, me, *args):
    raise Exception('unimpl')

  def __str__(self):
    return self.__class__.__name__


class Load(Instr):
  def apply(self, pe, me, *args):
    pe[args[0]] = me.load(pe['R1'], args[1])  # all loads implicitly get R1, but set a defined register


class LoadI(Instr):
  def apply(self, pe, me, *args):
    pe[args[0]] = int(args[1])


class Jump(Instr):
  labels = {
    'treenode': 3,
    'leafnode': 12,
    'rightnode': 14,
  }

  def apply(self, pe, me, *args):
    pe._ip = Jump.labels[args[0]]


class And(Instr):
  def apply(self, pe, me, *args):
    pe['ZF'] = pe[args[0]] & pe[args[1]]


class JNZ(Jump):
  def apply(self, pe, me, *args):
    nz = pe['ZF']
    pe['ZF'] = 0  # clear the bit
    if nz:
      super(JNZ, self).apply(pe, me, *args)  # perform the jump


class SLI(Instr):
  def apply(self, pe, me, *args):
    pe[args[0]] <<= int(args[1])


class AddI(Instr):
  def apply(self, pe, me, *args):
    pe[args[0]] += int(args[1])


class AddF(Instr):
  def apply(self, pe, me, *args):
    pe[args[0]] += pe[args[1]]


class Cmp(Instr):
  def apply(self, pe, me, *args):
    pe['ZF'] = int(pe[args[0]] > pe[args[1]])
