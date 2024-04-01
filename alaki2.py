#
# 
#

from collections import namedtuple
import sqlite3


class AccessFrequencies:
    """This class is NOT thread-safe."""

    def __init__(self, *, bytes_count = 2) -> None:
        """Initializes a new instance of this type:
        * `bytes_count`: the length of each frequency
        """
        self._nBytes = bytes_count
        """The length of each frequency when it comes to `bytes`
        conversions.
        """
        self._freqs = [0] * 24
        """A list of 24 integers for number of access in each hour."""
    
    def __repr__(self) -> str:
        return (f"<'{self.__class__.__qualname__}' object, "
            f"frequencies={self._freqs}>")
    
    @property
    def BytesCount(self) -> int:
        """Gets or sets number of bytes (length) for each frequency."""
        return self._nBytes
    
    @BytesCount.setter
    def BytesCount(self, __n: int, /) -> None:
        if not isinstance(__n, int):
            raise TypeError('number of bytes must be a positive integer')
        if __n < 1:
            raise ValueError('number of bytes must be a positive integer')
        self._nBytes = __n
    
    @property
    def Bytes(self) -> bytes:
        """Gets or sets the access frequencies as serialized (raw) data.
        Suitable for I/O operations. If provided bytes object is less than
        necessary, the remaining part is filled with seros.
        """
        from io import BytesIO
        with BytesIO() as bufferObj:
            for freq in self._freqs:
                bufferObj.write(freq.to_bytes(self._nBytes))
            buffer = bufferObj.getvalue()
        return buffer

    @Bytes.setter
    def Bytes(self, __bytes: bytes, /) -> None:
        # Declaring of variables --------------------------
        from io import BytesIO
        # Converting bytes -> list[int] -------------------
        if not isinstance(__bytes, bytes):
            raise TypeError(
                "setting 'Bytes' property requires a bytes object")
        freqs = [0] * 24
        with BytesIO(__bytes) as bufferObj:
            for idx in range(24):
                freqs[idx] = int.from_bytes(bufferObj.read(self._nBytes))
        self._freqs = freqs


UserData = namedtuple(
    'UserData',
    'user_id, first_name, last_name, phone, frequencies')


def main() -> None:
    selectSql = """
        SELECT
            user_id, first_name, last_name, phone, frequencies
        FROM
            users
        WHERE
            user_id = ?
    """
    with sqlite3.connect('db.db3') as conn:
        cur = conn.cursor()
        cur = cur.execute(selectSql, (100100,))
        userData = UserData(*cur.fetchone())
        print(userData)


if __name__ == '__main__':
    freqs = AccessFrequencies()
    freqs.Bytes = b'\x01\x02\x02\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01'
    print(freqs._freqs)
    print(freqs.Bytes)
    main()
