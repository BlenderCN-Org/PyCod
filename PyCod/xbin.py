import struct
import os
from io import BytesIO

from . import _lz4 as lz4

LOG_BLOCKS = False
LZ4_VERBOSE = False

__LZ4_DISPLAY_SUPPORT_INFO__ = True


def print_lz4_support_info(force=False):
    '''
    Print the lz4 support info
    'force' can be used to force the info to print again after the first time
    '''
    global __LZ4_DISPLAY_SUPPORT_INFO__
    if __LZ4_DISPLAY_SUPPORT_INFO__ | force:
        print(lz4.support_info)
        __LZ4_DISPLAY_SUPPORT_INFO__ = False


def padded(size):
    return (size + 0x3) & 0xFFFFFFFFFFFFFC


def __clamp_float_to_short__(value, clamp=(-32768, 32767)):
    return max(min(int(value * clamp[1]), clamp[1]), clamp[0])


def __str2bytes__(string):
    return bytearray(str(string).encode('utf-8'))


class XBlock(object):
    '''
    This is a namespace-like class that contains all of the block read/write
    functions for the xbins
    '''
    # #### #
    # Read #
    # #### #

    @staticmethod
    def LoadString(file):
        bytes = b''
        b = file.read(1)
        while not b == b'\x00':
            bytes += b
            b = file.read(1)
        return bytes.decode("utf-8")

    @staticmethod
    def LoadString_Aligned(file):
        start = file.tell()
        string = XBlock.LoadString(file)
        file.seek(start + padded(file.tell() - start))
        return string

    @staticmethod
    def LoadInt16Block(file):
        data = file.read(2)
        return struct.unpack('h', data)[0]

    @staticmethod
    def LoadUInt16Block(file):
        data = file.read(2)
        return struct.unpack('H', data)[0]

    @staticmethod
    def LoadInt32Block(file):
        file.seek(file.tell() + 2)
        data = file.read(4)
        return struct.unpack('i', data)[0]

    @staticmethod
    def LoadCommentBlock(file):
        start = file.tell() - 2
        file.seek(start + 4)
        string = XBlock.LoadString(file)
        file.seek(start + padded(file.tell() - start))
        return string

    @staticmethod
    def LoadBoneBlock(file):
        start = file.tell() - 2
        file.seek(start + 4)
        data = file.read(8)
        result = struct.unpack('ii', data)
        result = (result[0], result[1], XBlock.LoadString(file))
        file.seek(start + padded(file.tell() - start))
        return result

    @staticmethod
    def LoadFloatBlock(file):
        start = file.tell() - 2
        file.seek(start + 4)
        data = file.read(4)
        result = struct.unpack('f', data)
        file.seek(start + padded(file.tell() - start))
        return result

    @staticmethod
    def LoadVec2Block(file):
        start = file.tell() - 2
        file.seek(start + 4)
        data = file.read(8)
        result = struct.unpack('ff', data)
        file.seek(start + padded(file.tell() - start))
        return result

    @staticmethod
    def LoadVec3Block(file):
        start = file.tell() - 2
        file.seek(start + 4)
        data = file.read(12)
        result = struct.unpack('fff', data)
        file.seek(start + padded(file.tell() - start))
        return result

    @staticmethod
    def LoadShortVec3Block(file):
        data = file.read(6)
        x, y, z = struct.unpack('hhh', data)
        return (x / 32767.0, y / 32767.0, z / 32767.0)

    @staticmethod
    def LoadVec4Block(file):
        start = file.tell() - 2
        file.seek(start + 4)
        data = file.read(16)
        result = struct.unpack('ffff', data)
        file.seek(start + padded(file.tell() - start))
        return result

    @staticmethod
    def LoadVertexWeightBlock(file):
        data = file.read(6)
        result = struct.unpack('=hf', data)
        return result

    @staticmethod
    def LoadTriangleBlock(file):
        data = file.read(2)
        result = struct.unpack('BB', data)
        return result

    @staticmethod
    def LoadTriangle16Block(file):
        file.seek(file.tell() + 2)
        data = file.read(4)
        result = struct.unpack('HH', data)
        return result

    @staticmethod
    def LoadColorBlock(file):
        file.seek(file.tell() + 2)
        data = file.read(4)
        r, g, b, a = struct.unpack('BBBB', data)
        return (r / 255.0, g / 255.0, b / 255.0, a / 255.0)

    @staticmethod
    def LoadUVBlock(file):
        data = file.read(10)
        result = struct.unpack('=hff', data)
        # Ignore UV layer for now
        return (result[1], result[2])

    @staticmethod
    def LoadObjectBlock(file):
        start = file.tell() - 2
        data = file.read(2)
        result = struct.unpack('h', data) + (XBlock.LoadString(file),)
        file.seek(start + padded(file.tell() - start))
        return result

    @staticmethod
    def LoadMaterialBlock(file):
        # Include after to allow xmodel object to serialize
        from .xmodel import deserialize_image_string
        start = file.tell() - 2
        data = file.read(2)
        name = XBlock.LoadString_Aligned(file)
        _type = XBlock.LoadString_Aligned(file)
        imgs = deserialize_image_string(XBlock.LoadString_Aligned(file))
        result = struct.unpack('h', data) + (name, _type, imgs)
        file.seek(start + padded(file.tell() - start))
        return result

    @staticmethod
    def LoadNoteFrameBlock(file):
        start = file.tell() - 2
        file.seek(start + 4)
        data = file.read(4)
        result = struct.unpack('i', data) + (XBlock.LoadString(file),)
        file.seek(start + padded(file.tell() - start))
        return result

    # ############### #
    # Write Functions #
    # ############### #
    @staticmethod
    def WriteString(file, string):
        file.write(string + '\0')

    @staticmethod
    def WriteString_Aligned(file, string):
        file.write(string + '\0')
        size = len(string) + 1
        pad = padded(size) - size
        file.write("\0" * pad)

    # Meta Generic

    @staticmethod
    def WriteMetaObjectInfo(file, _hash, index, name):
        name = __str2bytes__(name)
        data = struct.pack('Hh%ds' % (padded(len(name) + 1)),
                           _hash, index, name)
        file.write(data)

    @staticmethod
    def WriteMetaInt16Block(file, _hash, value=0):
        data = struct.pack('Hh', _hash, value)
        file.write(data)

    @staticmethod
    def WriteMetaUInt16Block(file, _hash, value=0):
        data = struct.pack('HH', _hash, value)
        file.write(data)

    @staticmethod
    def WriteMetaInt32Block(file, _hash, value=0):
        data = struct.pack('HxxI', _hash, value)
        file.write(data)

    @staticmethod
    def WriteMetaFloatBlock(file, _hash, flt):
        data = struct.pack('Hxxf', _hash, flt)
        file.write(data)

    @staticmethod
    def WriteMetaVec2Block(file, _hash, vec):
        data = struct.pack('Hxxff', _hash, *vec)
        file.write(data)

    @staticmethod
    def WriteMetaVec3Block(file, _hash, vec):
        data = struct.pack('Hxxfff', _hash, *vec)
        file.write(data)

    @staticmethod
    def WriteMetaVec4Block(file, _hash, vec):
        data = struct.pack('Hxxffff', _hash, *vec)
        file.write(data)

    # Generic

    @staticmethod
    def WriteCommentBlock(file, comment):
        comment = bytearray(comment.encode('utf-8'))
        data = struct.pack('Hxx%ds' % (len(comment) + 1), 0xC355, comment)
        file.write(data)

    @staticmethod
    def WriteModelBlock(file):
        data = struct.pack('Hxx', 0x46C8)
        file.write(data)

    @staticmethod
    def WriteAnimBlock(file):
        data = struct.pack('Hxx', 0x7AAC)
        file.write(data)

    @staticmethod
    def WriteVersionBlock(file, version):
        data = struct.pack('Hh', 0x24D1, version)
        file.write(data)

    @staticmethod
    def WriteOffsetBlock(file, offset):
        data = struct.pack('Hxxfff', 0x9383, *offset)
        file.write(data)

    @staticmethod
    def WriteMatrixBlock(file, matrix):
        m = [
            tuple([__clamp_float_to_short__(v) for v in matrix[0]]),
            tuple([__clamp_float_to_short__(v) for v in matrix[1]]),
            tuple([__clamp_float_to_short__(v) for v in matrix[2]]),
        ]

        data = struct.pack('Hhhh', 0xDCFD, *m[0])
        data += struct.pack('Hhhh', 0xCCDC, *m[1])
        data += struct.pack('Hhhh', 0xFCBF, *m[2])
        file.write(data)

    # Model-specific

    @staticmethod
    def WriteBoneCountBlock(file, bone_count):
        XBlock.WriteMetaInt16Block(file, 0x76BA, bone_count)

    @staticmethod
    def WriteBoneInfoBlock(file, bone_index, bone):
        name = __str2bytes__(bone.name)
        data = struct.pack('Hxxii%ds' % padded(len(name) + 1), 0xF099,
                           bone_index, bone.parent, name)
        file.write(data)

    @staticmethod
    def WriteCosmeticInfoBlock(file, cosmetic_count):
        XBlock.WriteMetaInt32Block(file, 0x7836, cosmetic_count)

    @staticmethod
    def WriteBoneIndexBlock(file, index):
        XBlock.WriteMetaInt16Block(file, 0xDD9A, index)

    @staticmethod
    def WriteVertex16Count(file, vert_count):
        XBlock.WriteMetaUInt16Block(file, 0x950D, vert_count)

    @staticmethod
    def WriteVertex32Count(file, vert_count):
        XBlock.WriteMetaInt32Block(file, 0x2AEC, vert_count)

    @staticmethod
    def WriteVertex16Index(file, vert_index):
        XBlock.WriteMetaUInt16Block(file, 0x8F03, vert_index)

    @staticmethod
    def WriteVertex32Index(file, vert_index):
        XBlock.WriteMetaInt32Block(file, 0xB097, vert_index)

    @staticmethod
    def WriteVertexWeightBlock(file, weight):
        data = struct.pack('Hhf', 0xF1AB, *weight)
        file.write(data)

    @staticmethod
    def WriteFaceInfoBlock(file, face):
        # Check for over the byte limit
        if face.mesh_id > 255 or face.material_id > 255:
            data = struct.pack('HHHH', 0x6711, 0x0, face.mesh_id, face.material_id)
            file.write(data)
        else:
            data = struct.pack('HBB', 0x562F, face.mesh_id, face.material_id)
            file.write(data)

    @staticmethod
    def WriteFaceVertexNormalBlock(file, normal):
        packed = tuple([__clamp_float_to_short__(n) for n in normal])
        data = struct.pack('Hhhh', 0x89EC, *packed)
        file.write(data)

    @staticmethod
    def WriteColorBlock(file, color):
        rgb = tuple([int(c * 255) for c in color])
        data = struct.pack('HxxBBBB', 0x6DD8, *rgb)
        file.write(data)

    @staticmethod
    def WriteFaceVertexUVBlock(file, layer, uv):
        data = struct.pack('Hhff', 0x1AD4, layer, *uv)
        file.write(data)

    @staticmethod
    def WriteMaterialInfoBlock(file,
                               material_index,
                               material,
                               extended_features=True):
        from .xmodel import serialize_image_string
        strings = (__str2bytes__(material.name),
                   __str2bytes__(material.type),
                   __str2bytes__(serialize_image_string(
                       material.images, extended_features=True))
                   )
        sizes = tuple([padded(len(s) + 1) for s in strings])
        data = struct.pack('Hh%ds%ds%ds' %
                           sizes, 0xA700, material_index, *strings)
        file.write(data)

    # Anim-specific

    @staticmethod
    def WritePartCount(file, part_count):
        data = struct.pack('Hh', 0x9279, part_count)
        file.write(data)

    @staticmethod
    def WritePartInfo(file, index, name):
        XBlock.WriteMetaObjectInfo(file, 0x360B, index, name)

    @staticmethod
    def WritePartIndex(file, index):
        data = struct.pack('Hh', 0x745A, index)
        file.write(data)

    @staticmethod
    def WriteFramerate(file, framerate):
        data = struct.pack('Hh', 0x92D3, int(framerate))
        file.write(data)

    @staticmethod
    def WriteFrameCount(file, frame_count):
        data = struct.pack('Hxxi', 0xB917, frame_count)
        file.write(data)

    @staticmethod
    def WriteFrameIndex(file, frame):
        data = struct.pack('Hxxi', 0xC723, frame)
        file.write(data)

    @staticmethod
    def WriteNoteFrame(file, note):
        string = __str2bytes__(note.string)
        data = struct.pack('Hxxi%ds' % (len(string) + 1),
                           0x1675, int(note.frame), string)
        end = file.tell() + len(data)
        file.write(data)
        file.write("\0" * (padded(end) - end))


class XBinIO(object):
    __slots__ = ('version')

    def __init__(self): return

    @staticmethod
    def __decompress_internal__(file, dump=False):
        filepath = os.path.realpath(file.name)
        bin_magic = file.read(5)

        if bin_magic != b'*LZ4*':
            raise ValueError("Bad magic %s expected b'*LZ4*'" %
                             repr(bin_magic))

        if LZ4_VERBOSE:
            print_lz4_support_info()
            print("LZ4: Decompressing File: '%s'" % os.path.basename(filepath))
        data = lz4.uncompress(file.read())
        if LZ4_VERBOSE:
            print('LZ4: Done')
        file.close()
        if dump:
            dump_name = os.path.splitext(filepath)[0]
            dump_file = open("%s.dump" % dump_name, "wb")
            dump_file.write(data)
            dump_file.close()

        return BytesIO(data)

    @staticmethod
    def __compress_internal__(in_file, out_file, close_files=True):
        if LZ4_VERBOSE:
            print_lz4_support_info()
            print('LZ4: Encoding')
        in_file.seek(0, os.SEEK_END)
        uncompressed_size = in_file.tell()
        in_file.seek(0, os.SEEK_SET)
        compressed_data = lz4.compress(in_file.read())
        if close_files:
            in_file.close()
        if LZ4_VERBOSE:
            print('LZ4: Done')
        out_file.write(b'*LZ4*')
        out_file.write(struct.pack('I', uncompressed_size))
        out_file.write(compressed_data)
        if close_files:
            out_file.close()

    def __xbin_loadfile_internal__(self, file, expected_type):
        '''
        Load an x*_bin file
        file is a handle to the file
        target_type = 'ANIM' or 'MODEL'
        '''

        # Ensure that these modules can inherit from us by delay loading
        from . import xmodel as XModel
        from . import xanim as XAnim

        class LoadState(object):
            __slots__ = ('active_thing', 'active_tri',
                         'active_frame', 'asset_type')

            def __init__(self):
                self.active_thing = None
                self.active_tri = None
                self.active_frame = None
                self.asset_type = None

        state = LoadState()
        dummy_mesh = XModel.Mesh("$default")

        def InitModel(file):
            XBlock.LoadInt16Block(file)
            state.asset_type = 'MODEL'
            if expected_type != state.asset_type:
                raise TypeError("Found %s asset. Expected %s" %
                                (state.asset_type, expected_type))

        def InitAnim(file):
            XBlock.LoadInt16Block(file)
            state.asset_type = 'ANIM'
            if expected_type != state.asset_type:
                raise TypeError("Found %s asset. Expected %s" %
                                (state.asset_type, expected_type))

        def LoadBoneCount(file):
            self.bones = [None] * XBlock.LoadInt16Block(file)

        def LoadCosmeticCount(file):
            self.cosmetics = XBlock.LoadInt32Block(file)

        def LoadBoneInfo(file):
            index, parent, name = XBlock.LoadBoneBlock(file)
            bone = XModel.Bone(name, parent)
            if index >= (len(self.bones) - self.cosmetics):
                bone.cosmetic = True
            self.bones[index] = bone

        def LoadBoneIndex(file):
            index = XBlock.LoadInt16Block(file)
            bone = self.bones[index]
            bone.matrix = []
            state.active_thing = bone

        def LoadOffset(file):
            data = XBlock.LoadVec3Block(file)
            state.active_thing.offset = data
            return data

        def LoadBoneScale(file):
            data = XBlock.LoadVec3Block(file)
            state.active_thing.scale = data

        def LoadBoneMatrix(file):
            data = XBlock.LoadShortVec3Block(file)
            state.active_thing.matrix.append(data)
            return data

        def LoadVertexCount(file):
            dummy_mesh.verts = [None] * XBlock.LoadUInt16Block(file)

        def LoadVertex32Count(file):
            dummy_mesh.verts = [None] * XBlock.LoadInt32Block(file)

        def LoadVertexIndex(file):
            index = XBlock.LoadUInt16Block(file)
            if state.active_tri is None:
                vertex = XModel.Vertex()
                dummy_mesh.verts[index] = vertex
                state.active_thing = vertex
            else:
                face_vert = XModel.FaceVertex(index)
                state.active_tri.indices.append(face_vert)
                state.active_thing = face_vert

        def LoadVertex32Index(file):
            index = XBlock.LoadInt32Block(file)
            if state.active_tri is None:
                vertex = XModel.Vertex()
                dummy_mesh.verts[index] = vertex
                state.active_thing = vertex
            else:
                face_vert = XModel.FaceVertex(index)
                state.active_tri.indices.append(face_vert)
                state.active_thing = face_vert

        def LoadVertexWeightCount(file):
            XBlock.LoadInt16Block(file)
            state.active_thing.weights = []

        def LoadVertexWeight(file):
            state.active_thing.weights.append(
                XBlock.LoadVertexWeightBlock(file))

        def LoadTriCount(file):
            XBlock.LoadInt32Block(file)
            dummy_mesh.faces = []

        def LoadTriInfo(file):
            object_index, material_index = XBlock.LoadTriangleBlock(file)
            tri = XModel.Face(object_index, material_index)
            tri.indices = []
            dummy_mesh.faces.append(tri)
            state.active_tri = tri

        def LoadTri16Info(file):
            object_index, material_index = XBlock.LoadTriangle16Block(file)
            tri = XModel.Face(object_index, material_index)
            tri.indices = []
            dummy_mesh.faces.append(tri)
            state.active_tri = tri

        def LoadTriVertNormal(file):
            state.active_thing.normal = XBlock.LoadShortVec3Block(file)

        def LoadTriVertColor(file):
            state.active_thing.color = XBlock.LoadColorBlock(file)

        def LoadTriVertUV(file):
            state.active_thing.uv = XBlock.LoadUVBlock(file)

        def LoadObjectCount(file):
            self.meshes = [None] * XBlock.LoadInt16Block(file)

        def LoadObjectInfo(file):
            index, name = XBlock.LoadObjectBlock(file)
            self.meshes[index] = XModel.Mesh(name)

        def LoadMaterialCount(file):
            self.materials = [None] * XBlock.LoadInt16Block(file)

        def LoadMaterialInfo(file):
            index, name, _type, images = XBlock.LoadMaterialBlock(file)
            material = XModel.Material(name, _type, images)
            self.materials[index] = material
            state.active_thing = material

        def LoadMaterialTransparency(file):
            state.active_thing.transparency = XBlock.LoadVec4Block(file)

        def LoadMaterialAmbientColor(file):
            state.active_thing.color_ambient = XBlock.LoadVec4Block(file)

        def LoadMaterialIncandescence(file):
            state.active_thing.incandescence = XBlock.LoadVec4Block(file)

        def LoadMaterialCoeffs(file):
            state.active_thing.coeffs = XBlock.LoadVec2Block(file)

        def LoadMaterialGlow(file):
            state.active_thing.glow = XBlock.LoadVec2Block(file)

        def LoadMaterialRefractive(file):
            state.active_thing.refractive = XBlock.LoadVec2Block(file)

        def LoadMaterialSpecularColor(file):
            state.active_thing.color_specular = XBlock.LoadVec4Block(file)

        def LoadMaterialReflectiveColor(file):
            state.active_thing.color_reflective = XBlock.LoadVec4Block(file)

        def LoadMaterialReflective(file):
            state.active_thing.reflective = XBlock.LoadVec2Block(file)

        def LoadMaterialBlinn(file):
            state.active_thing.blinn = XBlock.LoadVec2Block(file)

        def LoadMaterialPhong(file):
            state.active_thing.phong = XBlock.LoadFloatBlock(file)

        # Animation
        def LoadPartCount(file):
            self.parts = [None] * XBlock.LoadInt16Block(file)

        def LoadPartInfo(file):
            index, name = XBlock.LoadObjectBlock(file)
            self.parts[index] = XAnim.PartInfo(name)

        def LoadPartIndex(file):
            index = XBlock.LoadInt16Block(file)
            frame_part = XAnim.FramePart(matrix=[])
            state.active_frame.parts[index] = frame_part
            state.active_thing = frame_part
            return index

        def LoadFramerate(file):
            self.framerate = XBlock.LoadInt16Block(file)

        def LoadFrameCount(file):
            XBlock.LoadInt32Block(file)

        def LoadFrameIndex(file):
            frame = XAnim.Frame(XBlock.LoadInt32Block(file))
            frame.parts = [None] * len(self.parts)
            state.active_frame = frame
            self.frames.append(frame)
            return frame.frame

        def LoadNotetracksBegin(file):
            # Activate a dummy frame, as notetracks sometimes contain part
            # indices.
            # If the active_frame isn't reset, the bone data for
            #  the most recently loaded frame will be corrupted
            dummy_frame = XAnim.Frame(-1)
            dummy_frame.parts = [None] * len(self.parts)
            state.active_frame = dummy_frame
            XBlock.LoadInt16Block(file)

        def LoadNoteFrame(file):
            frame, string = XBlock.LoadNoteFrameBlock(file)
            self.notes.append(XAnim.Note(frame, string))

        hashmap = {
            0xC355: ("Comment block", XBlock.LoadCommentBlock),
            0x46C8: ("Model identification block", InitModel),
            0x7AAC: ("Animation block", InitAnim),
            0x24D1: ("Version block", XBlock.LoadInt16Block),

            # Model Specific
            0x76BA: ("Bone count block", LoadBoneCount),
            0x7836: ("Cosmetic bone count block", LoadCosmeticCount),
            0xF099: ("Bone block", LoadBoneInfo),
            0xDD9A: ("Bone index block", LoadBoneIndex),
            0x9383: ("Vert / Bone offset block", LoadOffset),
            0x1C56: ("Bone scale block", LoadBoneScale),
            0xDCFD: ("Bone x matrix", LoadBoneMatrix),
            0xCCDC: ("Bone y matrix", LoadBoneMatrix),
            0xFCBF: ("Bone z matrix", LoadBoneMatrix),

            0x950D: ("Number of verts", LoadVertexCount),
            0x2AEC: ("Number of verts32", LoadVertex32Count),
            0x8F03: ("Vert info block marker", LoadVertexIndex),
            0xB097: ("Vert32 info block marker", LoadVertex32Index),
            0xEA46: ("Vert weighted bones count", LoadVertexWeightCount),
            0xF1AB: ("Vert bone weight info", LoadVertexWeight),

            0xBE92: ("Number of faces block", LoadTriCount),
            0x562F: ("Triangle info block", LoadTriInfo),
            0x6711: ("Triangle info (16) block", LoadTri16Info),
            0x89EC: ("Normal info", LoadTriVertNormal),
            0x6DD8: ("Color info", LoadTriVertColor),
            0x1AD4: ("UV info", LoadTriVertUV),

            0x62AF: ("Number of objects block", LoadObjectCount),
            0x87D4: ("Object info block", LoadObjectInfo),

            0xA1B2: ("Number of materials", LoadMaterialCount),
            0xA700: ("Material info block", LoadMaterialInfo),
            0x6DAB: ("Material transparency", LoadMaterialTransparency),
            0x37FF: ("Material ambient color", LoadMaterialAmbientColor),
            0x4265: ("Material incandescence", LoadMaterialIncandescence),
            0xC835: ("Material coeffs", LoadMaterialCoeffs),
            0xFE0C: ("Material glow", LoadMaterialGlow),
            0x7E24: ("Material refractive", LoadMaterialRefractive),
            0x317C: ("Material specular color", LoadMaterialSpecularColor),
            0xE593: ("Material reflective color", LoadMaterialReflectiveColor),
            0x7D76: ("Material reflective", LoadMaterialReflective),
            0x83C7: ("Material blinn", LoadMaterialBlinn),
            0x5CD2: ("Material phong", LoadMaterialPhong),

            # Animation Specific
            0x9279: ("NumParts block", LoadPartCount),
            0x360B: ("Part info block", LoadPartInfo),
            0x745A: ("Part index block", LoadPartIndex),
            0x92D3: ("Framerate block", LoadFramerate),
            0xB917: ("NumFrames block", LoadFrameCount),
            0xC723: ("Frame block", LoadFrameIndex),

            0xC7F3: ("Notetrack section block", LoadNotetracksBegin),
            0x9016: ("NumTracks block", XBlock.LoadInt16Block),
            0x7A6C: ("NumKeys block", XBlock.LoadInt16Block),
            0x4643: ("Notetrack block", XBlock.LoadInt16Block),
            0x1675: ("Note frame block", LoadNoteFrame),

            # Misc (Unimplemented)
            0xBCD4: ("FIRSTFRAME", None),
            0x1FC2: ("NUMSBONES", None),
            0xB35E: ("NUMSWEIGHTS", None),
            0xEF69: ("QUATERNION", None),
            0xA65B: ("NUMIKPITCHLAYERS", None),
            0x1D7D: ("IKPITCHLAYER", None),
            0xA58B: ("ROTATION", None),
            0x6EEE: ("EXTRA", None)
        }

        # Read all blocks
        data = file.read(2)
        while data:
            block_hash = struct.unpack('H', data)[0]
            if block_hash in hashmap:
                offset = file.tell()
                data = hashmap[block_hash]
                if data[1] is None:
                    raise NotImplementedError(
                        "Unimplemented Block '%s' at 0x%X" %
                        (data[0], offset))
                    break
                else:
                    if LOG_BLOCKS:
                        print("Loading Block: '%s' at 0x%X" %
                              (data[0], offset))
                    val = data[1](file)
                    if LOG_BLOCKS:
                        print("        Data: %s" % repr(val))

                # Read the next block hash
                data = file.read(2)
            else:
                offset = file.tell() - 2
                raise ValueError("Unknown Block Hash 0x%X at 0x%X" %
                                 (block_hash, offset))
                break

        # Return the dummy mesh for splitting if we imported a model
        if state.asset_type == 'MODEL':
            return dummy_mesh

    def __xbin_writefile_model_internal__(self, filepath, version=7,
                                          extended_features=True,
                                          header_message=""):
        model = self

        real_file = open(filepath, "wb")
        file = BytesIO()
        version = 7
        if header_message != '':
            XBlock.WriteCommentBlock(file, header_message)
        XBlock.WriteModelBlock(file)
        XBlock.WriteVersionBlock(file, version)

        cosmetic_count = len([bone for bone in self.bones if bone.cosmetic])

        XBlock.WriteBoneCountBlock(file, len(model.bones))
        if cosmetic_count > 0:
            XBlock.WriteCosmeticInfoBlock(file, cosmetic_count)

        for bone_index, bone in enumerate(model.bones):
            XBlock.WriteBoneInfoBlock(file, bone_index, bone)

        for bone_index, bone in enumerate(model.bones):
            XBlock.WriteBoneIndexBlock(file, bone_index)
            XBlock.WriteOffsetBlock(file, bone.offset)
            XBlock.WriteMetaVec3Block(file, 0x1C56, bone.scale)
            XBlock.WriteMatrixBlock(file, bone.matrix)

        # Used to offset the vertex indices for each mesh
        vert_offsets = [0]
        for mesh in model.meshes:
            prev_index = len(vert_offsets) - 1
            vert_offsets.append(vert_offsets[prev_index] + len(mesh.verts))

        vert_count = vert_offsets[len(vert_offsets) - 1]

        if version == 7 and vert_count > 0xFFFF:
            WriteVertexCountBlock = XBlock.WriteVertex32Count
            WriteVertexIndexBlock = XBlock.WriteVertex32Index
        else:
            WriteVertexCountBlock = XBlock.WriteVertex16Count
            WriteVertexIndexBlock = XBlock.WriteVertex16Index

        WriteVertexCountBlock(file, vert_count)
        for mesh_index, mesh in enumerate(model.meshes):
            vert_offset = vert_offsets[mesh_index]
            for vert_index, vert in enumerate(mesh.verts):
                WriteVertexIndexBlock(file, vert_index + vert_offset)
                XBlock.WriteOffsetBlock(file, vert.offset)
                XBlock.WriteMetaInt16Block(file, 0xEA46, len(vert.weights))
                for weight in vert.weights:
                    XBlock.WriteVertexWeightBlock(file, weight)

        # Faces
        face_count = sum([len(mesh.faces) for mesh in model.meshes])
        XBlock.WriteMetaInt32Block(file, 0xBE92, face_count)
        for mesh_index, mesh in enumerate(model.meshes):
            vert_offset = vert_offsets[mesh_index]
            for face in mesh.faces:
                XBlock.WriteFaceInfoBlock(file, face)
                for i in range(3):
                    ind = face.indices[i]
                    WriteVertexIndexBlock(file, ind.vertex + vert_offset)
                    XBlock.WriteFaceVertexNormalBlock(file, ind.normal)
                    XBlock.WriteColorBlock(file, ind.color)
                    XBlock.WriteFaceVertexUVBlock(file, 1, ind.uv)

        # Objects
        XBlock.WriteMetaInt16Block(file, 0x62AF, len(model.meshes))
        for mesh_index, mesh in enumerate(model.meshes):
            XBlock.WriteMetaObjectInfo(file, 0x87D4, mesh_index, mesh.name)

        # Materials
        XBlock.WriteMetaInt16Block(file, 0xA1B2, len(model.materials))
        for material_index, material in enumerate(model.materials):
            XBlock.WriteMaterialInfoBlock(file, material_index,
                                          material, extended_features)

            XBlock.WriteColorBlock(file, material.color)
            XBlock.WriteMetaVec4Block(file, 0x6DAB, material.transparency)
            XBlock.WriteMetaVec4Block(file, 0x37FF, material.color_ambient)
            XBlock.WriteMetaVec4Block(file, 0x4265, material.incandescence)
            XBlock.WriteMetaVec2Block(file, 0xC835, material.coeffs)
            XBlock.WriteMetaVec2Block(file, 0xFE0C, material.glow)
            XBlock.WriteMetaVec2Block(file, 0x7E24, material.refractive)
            XBlock.WriteMetaVec4Block(file, 0x317C, material.color_specular)
            XBlock.WriteMetaVec4Block(file, 0xE593, material.color_reflective)
            XBlock.WriteMetaVec2Block(file, 0x7D76, material.reflective)
            XBlock.WriteMetaVec2Block(file, 0x83C7, material.blinn)
            XBlock.WriteMetaFloatBlock(file, 0x5CD2, material.phong)

        XBinIO.__compress_internal__(file, real_file, close_files=True)

    def __xbin_writefile_anim_internal__(self, filepath, version=3,
                                         header_message=""):
        anim = self
        real_file = open(filepath, "wb")
        file = BytesIO()
        if header_message != '':
            XBlock.WriteCommentBlock(file, header_message)
        XBlock.WriteAnimBlock(file)
        XBlock.WriteVersionBlock(file, 3)
        XBlock.WritePartCount(file, len(anim.parts))

        for part_index, part in enumerate(anim.parts):
            XBlock.WritePartInfo(file, part_index, part.name)

        XBlock.WriteFramerate(file, anim.framerate)
        XBlock.WriteFrameCount(file, len(anim.frames))

        for frame in anim.frames:
            XBlock.WriteFrameIndex(file, frame.frame)
            for part_index, part in enumerate(frame.parts):
                XBlock.WritePartIndex(file, part_index)
                XBlock.WriteOffsetBlock(file, part.offset)
                XBlock.WriteMatrixBlock(file, part.matrix)

        XBlock.WriteMetaInt16Block(file, 0x7A6C, len(anim.notes))
        if len(anim.notes):
            for note in anim.notes:
                XBlock.WriteNoteFrame(file, note)

        XBinIO.__compress_internal__(file, real_file, close_files=True)
