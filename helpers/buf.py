# helpers/buf.py
# for use in custom file formats

# bytes stored in little endian
# strings stored in UTF-8

def read_i32(file):
   """Reads a 4 byte signed integer from `file`."""
   return int.from_bytes(file.read(4), "little", signed=True)

def read_str(file):
   """Reads a string from `file`. Returns (str, len).

   struct str {
      len: i32,
      buf: char[len]
   }

   """
   len = read_i32(file)
   return ("" if len < 0 else file.read(len).decode("utf-8"), len)

def read_map_str_i32(file):
   """Reads a map<str, i32> from `file`.

   struct map<str, i32> {
      {str, i32},
      ...
   }

   Mapping ends when it encounters a negative-length str

   """
   mapping = dict()
   while True:
      str, len = read_str(file)
      if len < 0:
         break
      mapping[str] = read_i32(file)
   return mapping


def write_i32(file, i32):
   """Writes a 4 byte signed integer to `file`."""
   file.write(i32.to_bytes(4, "little", signed=True))

def write_str(file, str):
   """Writes a string to `file`. See read_str for struct format."""
   bytes = str.encode("utf-8")
   file.write(len(bytes).to_bytes(4, "little"))
   file.write(bytes)

def write_map_str_i32(file, mapping):
   """Writes a map<str, i32> to `file`. See read_map_str_i32 for struct format."""
   for k,v in mapping.items():
      write_str(file, k)
      write_i32(file, v)
   write_i32(file, -1) # negative length str
