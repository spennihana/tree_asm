from instr import Load, LoadI, Jump, And, JNZ, SLI, AddI, AddF, Cmp
class PE(object):

  INSTRS = {
    'l': Load(),
    'li': LoadI(),
    'jmp': Jump(),
    'and': And(),
    'jnz': JNZ(),
    'sli': SLI(),
    'addi': AddI(),
    'addf': AddF(),
    'cmp': Cmp(),
  }

  def __init__(self, N, mem):
    self._nfield = N
    self._mem = mem
    self._ip = 0  # instr pointer
    # 0 register            $0
    # Z flag                $Z
    # 1 mask on 16th bit    $1
    # N fields              F1 - FN
    # 1 result field        R0
    # 1 current node addr   R1
    # 1 for field ID        R2
    # 1 for field value     R3
    self._R = [0]*(1+1+1+N+1+(1+1+1))  # R1, R2, R3 refer to the last 3 regs
    self._R[2] = 1<<15
    self._im = []  # inst memory
    self._setup_instrs()

    # str to reg dict
    self.regs = {
      'S0': 0,
      'ZF': 1,
      'S1': 2,
      'R0': 1 + 1 + 1 + self._nfield,
      'R1': 1 + 1 + 1 + self._nfield + 1,
      'R2': 1 + 1 + 1 + self._nfield + 1 + 1,
      'R3': 1 + 1 + 1 + self._nfield + 1 + 1 + 1,
    }

  def _setup_instrs(self):
    self._im = [
    # loadroot
      'l R1 M[2]',   # load root instr
      'li R0 0',     # clear the contents of R0
      'li R1 0',     # clear R1
    # treenode
      'l R2 M[0]',  # load the field id
      'l R3 M[1]',  # load the field value
      'and R2 S1',  # check the is_leaf bit
      'jnz leafnode',
      'sli R1 1',       # start loading the next node by shifting R1 left 1 and adding 1
      'addi R1 1',      # R1 now contains addr of left child
      'cmp R[R2] R3',   # compare field value with node value
      'jnz rightnode',  # if greater, then need to add 1 to R1 for right child
      'jmp treenode',
    # leafnode
      'addf R0 R3',
      'exit',
    # rightnode
      'addi R1 1',      # R1 now contains addr of right child
      'jmp treenode'
    ]

  def proc_row(self, row):
    self._load_regs(row)
    self._ip=0
    instr = next(self)
    while instr!='exit':
      toks = self._decode(instr)
      self._exec(toks)
      instr = next(self)

  def __next__(self):
    instr = self._im[self._ip]
    self._ip += 1
    return instr

  def __setitem__(self, key, value):
    self._R[self.regs[key]] = value

  def __getitem__(self, item):
    if '[' in item:
      idx = (1+1+1) + self[item[item.index('[')+1:item.index(']')]]
      return self._R[idx]
    return self._R[self.regs[item]]

  def _decode(self, instr):
    toks = []
    start, x = 0, 0
    while x < len(instr):
      if instr[x] == ' ':
        toks += [instr[start:x]]
        start = x+1
      x += 1
    toks += [instr[start:x]]
    return toks

  def _exec(self, toks):
    PE.INSTRS[toks[0]].apply(self, self._mem, *toks[1:])

  def _load_regs(self, row):
    for i, r in enumerate(row):
      self._R[(1+1+1)+i] = r

class ME(object):
  def __init__(self):
    self._M = []

  # treenode structure:
  #  field_id + isleaf bit  (2 bytes, 15 bits for field addr + 1 isleaf bit)
  #  field_val (32 bit float, not missing)
  #  node_id  (4 byte)
  def load(self, node_idx, idx):
    idx = int(idx[idx.index('[')+1:idx.index(']')])
    return self._M[node_idx][idx]

def expect_equal(a1, a2):
  assert len(a1)==len(a2)
  assert set(a1) == set(a2)

def decode(instr):
  toks = []
  start, x = 0, 0
  while x < len(instr):
    if instr[x]==' ':
      toks += [instr[start:x]]
      start = x+1
    x+=1
  toks += [instr[start:x]]
  return toks

def test_simple_tree():
  me = ME()
  me._M = [    # [field_id/is_leaf, field_value, node_idx]
                 [2,1.8232,0],
          [1,45,1],       [3,0.2312,2],
  [1<<15,-2,3], [1<<15,1.23,4], [1<<15,-3,5], [1<<15, 2, 6]
]
  pe = PE(4, me)

  # check left subtree
  pe.proc_row([-1, 96, 1.77, -1])
  assert pe['R0'] == 1.23

  pe.proc_row([-1,44.9,1.8231,-1])
  assert pe['R0'] == -2

  # check right subtree
  pe.proc_row([-1,-1,2.8231,0.333])
  assert pe['R0'] == 2

  pe.proc_row([-1,-1,2.8231,0.144])
  assert pe['R0'] == -3

if __name__ == "__main__":
  test_simple_tree()