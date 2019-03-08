import math


class Device:

    def __init__(self, id):
        self.id = id
        self.topOffset = 0

    def get(self):

        it = Device(self.id)

        return it

    def process(self, pkt, at):

        service = pkt[at]

        at += 1

        if service == 0x2F:
            return self.processNeg(pkt, at)
        elif service == 0x2E:
            return self.processPing(pkt, at)
        elif service == 0x68:
            return self.processInfo(pkt, at)
        elif service == 0x73:
            return self.startConfirmOrOnline(service, pkt, at)
        elif service == 0x91:
            return self.latlon(self, service, pkt, at)
        elif service in [0x6C, 0x6D, 0x6F, 0x70, 0x71, 0x72]:
            pass
        else:
            pass
        
    def latlon(self, service, pkt, at):
        print(service)
        print(pkt)

    def startConfirmOrOnline(self, service, pkt, at):

        offset = pkt[at] << 24
        at += 1
        offset |= pkt[at] << 16
        at += 1
        offset |= pkt[at] << 8
        at += 1
        offset |= pkt[at]
        at += 1

        if service >= 0x70:
            return self.processConfirmed(service, offset, pkt, at)
        return self.processOnline(service, offset, pkt, at)

    def processNeg(self, pkt, at):
        return None

    def processPing(self, pkt, at):
        return 0x2E

    def processInfo(self, pkt, at):
        bgn = pkt[at] << 24
        at += 1
        bgn |= pkt[at] << 16
        at += 1
        bgn |= pkt[at] << 8
        at += 1
        bgn |= pkt[at]
        at += 1

        end = pkt[at] << 24
        at += 1
        end |= pkt[at] << 16
        at += 1
        end |= pkt[at] << 8
        at += 1
        end |= pkt[at]
        at += 1

        if self.topOffset < bgn:
            self.topOffset = bgn

        if self.topOffset >= end:
            return None

        tx = list()
        tx.append(0x6F)
        for byte in self.convertToByte():
            tx.append(byte)

        endOffset = self.topOffset + 10240

        for byte in self.convertToByte(endOffset):
            tx.append(byte)

        return tx

    def processConfirmed(self, service, offset, pkt, at):

        if (service & 1) != 0 and (offset > self.topOffset):
            self.topOffset = offset

        if offset == self.topOffset:
            self.processRecords(pkt, at)

        tx = []
        tx.append(0x72)
        for byte in self.convertToByte():
            tx.append(byte)

        return tx

    def convertToByte(self, data=None):

        if data:
            number_of_bytes = int(math.ceil(data.bit_length() / 8))
            x_bytes = data.to_bytes(number_of_bytes, byteorder='big')
        else:
            number_of_bytes = int(math.ceil(self.topOffset.bit_length() / 8))
            x_bytes = self.topOffset.to_bytes(number_of_bytes, byteorder='big')
            x_int = int.from_bytes(x_bytes, byteorder='big')

        return x_bytes

    def processOnline(self, service, offset, pkt, at):
        if offset == self.topOffset:
            self.processRecords(pkt, at)
            return None

        return 0x68

    def processRecords(self, pkt, at):

        lengthPkt = len(pkt)

        records = list()

        while lengthPkt > at:

            length = pkt[at]

            at += 1

            if length == 0:
                break

            if at + length > lengthPkt:
                break

            records.append(pkt[at:][:length])

            self.topOffset += (1 + length)
            at += length

        if records:

            dict = {
                'topOffset': self.topOffset,
                'records': records,
            }

            SaveRecordsTopOffsetToDb.save(dict)

            records.clear()


class SaveRecordsTopOffsetToDb(object):

    @staticmethod
    def save(data):

        from db.connect import pgconn, cursor
        import json
        from datetime import date

        query = "INSERT INTO records (top_offset, record, created_at, updated_at) VALUES (%s, %s, %s,%s);"
        data = (data['topOffset'], json.dumps(data['records']), date.today(), date.today())
        cursor.execute(query, data)
        pgconn.commit()


