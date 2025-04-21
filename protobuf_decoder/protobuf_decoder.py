import io
import struct


class Parser:
    def parse(self, hex_string):
        data = io.BytesIO(bytes.fromhex(hex_string))
        return self._parse_stream(data)

    def _parse_stream(self, stream):
        results = []

        while True:
            try:
                key = self._decode_varint(stream)
            except Exception:
                break

            field_number = key >> 3
            wire_type = key & 0x07

            if wire_type == 0:  # varint
                value = self._decode_varint(stream)
                results.append(Result(field=field_number, wire_type="varint", data=value))
            elif wire_type == 1:  # 64-bit
                value = stream.read(8)
                results.append(Result(field=field_number, wire_type="64bit", data=value))
            elif wire_type == 2:  # length-delimited
                length = self._decode_varint(stream)
                value = stream.read(length)
                nested = self._parse_stream(io.BytesIO(value))
                results.append(Result(field=field_number, wire_type="length_delimited", data=ParseResult(nested)))
            elif wire_type == 5:  # 32-bit
                value = stream.read(4)
                results.append(Result(field=field_number, wire_type="32bit", data=value))
            else:
                raise Exception(f"Unknown wire type: {wire_type}")

        return results

    def _decode_varint(self, stream):
        result = 0
        shift = 0
        while True:
            b = stream.read(1)
            if not b:
                raise EOFError("Unexpected end of stream")
            byte = b[0]
            result |= ((byte & 0x7F) << shift)
            if not (byte & 0x80):
                break
            shift += 7
        return result


class Result:
    def __init__(self, field, wire_type, data):
        self.field = field
        self.wire_type = wire_type
        self.data = data


class ParseResult:
    def __init__(self, results):
        self.results = results
