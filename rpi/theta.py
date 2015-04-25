#!/usr/bin/env python
# coding: UTF-8

from __future__ import print_function
import socket
import struct
import sys

DEBUG = False
DEBUG2 = False

PTP_OC_GetDeviceInfo      = 0x1001
PTP_OC_OpenSession        = 0x1002
PTP_OC_CloseSession       = 0x1003
PTP_OC_GetStorageIDs      = 0x1004
PTP_OC_GetStorageInfo     = 0x1005
PTP_OC_GetNumObjects      = 0x1006
PTP_OC_GetObjectHandles   = 0x1007
PTP_OC_GetObjectInfo      = 0x1008
PTP_OC_GetObject          = 0x1009
PTP_OC_GetThumb           = 0x100A
PTP_OC_DeleteObject       = 0x100B
PTP_OC_InitiateCapture    = 0x100E
PTP_OC_GetDevicePropDesc  = 0x1014
PTP_OC_GetDevicePropValue = 0x1015
PTP_OC_SetDevicePropValue = 0x1016
PTP_OC_UnknownCommand     = 0x1022

PTP_RC_Undefined = 0x2000
PTP_RC_OK        = 0x2001

# Object Format Code
PTP_OFC_Undefined   = 0x3000
PTP_OFC_Association = 0x3001 
PTP_OFC_EXIF_JPEG   = 0x3801
PTP_OFC_JFIF        = 0x3808

PTP_EC_ObjectAdded       = 0x4002
PTP_EC_DevicePropChanged = 0x4006
PTP_EC_StoreFull         = 0x400a
PTP_EC_CaptureComplete   = 0x400d 


class ThetaError(Exception):
    pass


class PTP_IP(object):
    def __init__(self, host, name, GUID):
        '''Initialize'''
        self.host = host
        self.port = 15740
        self.name = name
        self.GUID = GUID
        self.command_sock = None
        self.event_sock = None

    def _open_connection(self):
        # Init_Command
        self.command_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.command_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        self.command_sock.settimeout(0.5)
        try:
            self.command_sock.connect((self.host, self.port))
        except (OSError, socket.error, socket.timeout):
            print('Connection failed', file=sys.stderr)
            return 0

        self._send_init_command_request(self.command_sock)
        result, self.session_id = self._get_session_id(self.command_sock)

        if not result:
            print('InitCommandRequest failed', file=sys.stderr)
            return 0

        #print('(session_id = %d)' % self.session_id

        # Init_Event
        self.event_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.event_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        self.event_sock.settimeout(0.5)
        try:
            self.event_sock.connect((self.host, self.port))
        except (OSError, socket.error, socket.timeout) as e:
            print(e, file=sys.stderr)
            print('Connection failed', file=sys.stderr)
            return 0

        self._send_init_event_request(self.event_sock, self.session_id)
        result = self._wait_init_event_ack(self.event_sock)
        if not result:
            print('InitEvetRequest failed', file=sys.stderr)
            return 0

        self.transaction_id = 0

        return self.session_id

    def _close_connection(self):
        if self.command_sock is not None:
            self.command_sock.shutdown(socket.SHUT_RDWR)
            self.command_sock.close()
            self.command_sock = None

        if self.event_sock is not None:
            self.event_sock.shutdown(socket.SHUT_RDWR)
            self.event_sock.close()
            self.event_sock = None

    def _get_device_info(self):
        #print('PTP_OC_GetDeviceInfo'
        self._send_ptp_command_request(self.command_sock, self.transaction_id,
                                    '', PTP_OC_GetDeviceInfo)
        self.transaction_id += 1
        result, args, payload = self._wait_ptp_command_response(self.command_sock)
        if result != PTP_RC_OK:
            print('Failed', file=sys.stderr)

    def _open_session(self):
        #print('PTP_OC_OpenSession'
        self._send_ptp_command_request(self.command_sock, self.transaction_id,
                                    '', PTP_OC_OpenSession, self.session_id)
        self.transaction_id += 1
        result, args, payload = self._wait_ptp_command_response(self.command_sock)
        if result != PTP_RC_OK:
            print('Failed', file=sys.stderr)
            return 0
        return 1

    def _close_session(self):
        #print('PTP_OC_CloseSession'
        self._send_ptp_command_request(self.command_sock, self.transaction_id,
                                    '', PTP_OC_CloseSession)
        self.transaction_id += 1
        result, args, payload = self._wait_ptp_command_response(self.command_sock)
        if result != PTP_RC_OK:
            print('Failed', file=sys.stderr)

    def _get_storage_ids(self):
        #print('PTP_OC_GetStorageIDs'
        self._send_ptp_command_request(self.command_sock, self.transaction_id,
                                    '', PTP_OC_GetStorageIDs)
        self.transaction_id += 1
        result, args, payload = self._wait_ptp_command_response(self.command_sock)
        if result != PTP_RC_OK:
            print('Failed', file=sys.stderr)
            return []
        return self._unpack_int32_array(payload)

    def _get_storage_info(self, storage_id):
        #print('PTP_OC_GetStorageInfo'
        self._send_ptp_command_request(self.command_sock, self.transaction_id,
                                    '', PTP_OC_GetStorageInfo, storage_id)
        self.transaction_id += 1
        result, args, payload = self._wait_ptp_command_response(self.command_sock)
        if result != PTP_RC_OK:
            print('Failed', file=sys.stderr)

    def _get_num_objects(self, storage_id, obj_format = 0, parent_obj = 0):
        #print('PTP_OC_GetNumObjects'
        self._send_ptp_command_request(self.command_sock, self.transaction_id,
                                    '', PTP_OC_GetNumObjects,
                                    storage_id, obj_format, parent_obj)
        self.transaction_id += 1
        result, args, payload = self._wait_ptp_command_response(self.command_sock)
        if result != PTP_RC_OK:
            print('Failed', file=sys.stderr)
            return 0
        return args[0]

    def _get_object_handles(self, storage_id, obj_format = 0, parent_obj = 0):
        #print('PTP_OC_GetObjectHandles'
        self._send_ptp_command_request(self.command_sock, self.transaction_id,
                                    '', PTP_OC_GetObjectHandles,
                                    storage_id, obj_format, parent_obj)
        self.transaction_id += 1
        result, args, payload = self._wait_ptp_command_response(self.command_sock)
        if result != PTP_RC_OK:
            print('Failed', file=sys.stderr)
            return []
        return self._unpack_int32_array(payload)

    def _get_object_info(self, obj_handle):
        #print('PTP_OC_GetObjectInfo'
        self._send_ptp_command_request(self.command_sock, self.transaction_id,
                                    '', PTP_OC_GetObjectInfo, obj_handle)
        self.transaction_id += 1
        result, args, payload = self._wait_ptp_command_response(self.command_sock)
        if result != PTP_RC_OK:
            print('Failed', file=sys.stderr)
            return []
        # return payload
        return self._unpack_object_info(payload)

    def _get_object(self, obj_handle):
        #print('PTP_OC_GetObject'
        self._send_ptp_command_request(self.command_sock, self.transaction_id,
                                    '', PTP_OC_GetObject, obj_handle)
        self.transaction_id += 1
        result, args, payload = self._wait_ptp_command_response(self.command_sock)
        if result != PTP_RC_OK:
            print('Failed', file=sys.stderr)
            return []
        return payload

    def _get_thumb(self, obj_handle):
        #print('PTP_OC_GetThumb'
        self._send_ptp_command_request(self.command_sock, self.transaction_id,
                                    '', PTP_OC_GetThumb, obj_handle)
        self.transaction_id += 1
        result, args, payload = self._wait_ptp_command_response(self.command_sock)
        if result != PTP_RC_OK:
            print('Failed', file=sys.stderr)
            return []
        return payload

    def _set_device_prop_value(self, prop_id, val):
        #print('PTP_OC_SetDevicePropValue'
        # payload = self._pack_int16(val)
        self._send_ptp_command_request(self.command_sock, self.transaction_id,
                                    val, PTP_OC_SetDevicePropValue, prop_id)
        self.transaction_id += 1
        result, args, payload = self._wait_ptp_command_response(self.command_sock)
        if not result:
            print('Failed', file=sys.stderr)
            return 0
        return 1

    def _initiate_capture(self):
        #print('Send PTP_OC_InitiateCapture'
        self._send_ptp_command_request(self.command_sock, self.transaction_id,
                                    '', PTP_OC_InitiateCapture, 0, 0)
        self.transaction_id += 1
        result, args, payload = self._wait_ptp_command_response(self.command_sock)
        if not result:
            print('Failed', file=sys.stderr)
            return 0

        #print('Wait PTP_EC_CaptureComplete'
        handle = 0
        for loop in range(0, 20):
            ptp_event, args = self._wait_ptp_event(self.event_sock)
            if ptp_event == PTP_EC_CaptureComplete:
                break
            elif ptp_event == PTP_EC_ObjectAdded:
                handle = args[0]

        return handle

    def _send_init_command_request(self, sock):
        #print('Send InitCommandRequest'
        payload = ''
        payload += self._pack_guid()
        payload += self._pack_string(self.name)
        payload += self._pack_int32(1)

        self._send_command(sock, 1, payload)

    def _get_session_id(self, sock):
        #print('Wait InitCommandAck'
        cmd_id, payload = self._receive_response(sock)
        if cmd_id != 2:
            print('failed', file=sys.stderr)
            return 0, 0

        session_id = self._unpack_int32(payload[0:4])
        target_GUID = self._unpack_guid(payload[4:20])
        target_name = self._unpack_string(payload[20:-4])
        # and unknown 4 bytes

        #print('Target GUID : %s' % target_GUID
        #print('Target Name : %s' % target_name

        return 1, session_id

    def _send_init_event_request(self, sock, session_id):
        #print('Send InitEventRequest'
        payload = ''
        payload += self._pack_int32(session_id)

        self._send_command(sock, 3, payload)

    def _wait_init_event_ack(self, sock):
        #print('Wait InitEventAck'
        # sock.settimeout(10)
        cmd_id, payload = self._receive_response(sock)
        if cmd_id != 4:
            print('failed', file=sys.stderr)
            return 0
        return 1

    def _send_ptp_command_request(self, sock, transaction_id,
                                  ptp_payload, ptp_cmd, *args, **kwargs):
        # Cmd_Request
        payload = ''
        payload += self._pack_int32(1)
        payload += self._pack_int16(ptp_cmd)
        payload += self._pack_int32(transaction_id)
        for arg in args:
            payload += self._pack_int32(arg)
        self._send_command(sock, 6, payload)

        if ptp_payload == '':
            return

        # Start_Data_Packet
        payload = ''
        payload += self._pack_int32(transaction_id)
        payload += self._pack_int32(len(ptp_payload))
        payload += self._pack_int32(0)
        self._send_command(sock, 9, payload)

        index = 0
        next_index = index + 200
        while index < len(ptp_payload):
            payload = ''
            payload += self._pack_int32(transaction_id)
            payload += ptp_payload[index:next_index]
            if next_index < len(ptp_payload):
                # Data_Packet
                self._send_command(sock, 10, payload)
            else:
                # End_Data_Packet
                self._send_command(sock, 12, payload)
            index = next_index
            next_index += 200

    def _wait_ptp_command_response(self, sock):
        cmd_id, payload = self._receive_response(sock)
        ptp_payload = ''
        if cmd_id == 9:
            # Start_Data_Packet
            transaction_id = self._unpack_int32(payload[0:4])
            ptp_payload_len = self._unpack_int32(payload[4:8])
            while True:
                # Data_Packet or End_Data_Packet
                cmd_id, payload = self._receive_response(sock)
                if cmd_id != 10 and cmd_id != 12:
                    return 0, None, None
                temp_id = self._unpack_int32(payload[0:4])
                if temp_id != transaction_id:
                    return 0, None, None
                ptp_payload += payload[4:]
                if len(ptp_payload) >= ptp_payload_len or cmd_id == 12:
                    break
                if DEBUG:
                    print('.')
            # Cmd_Response
            cmd_id, payload = self._receive_response(sock)

        if cmd_id != 7:
            return 0, None, None
        ptp_res = self._unpack_int16(payload[0:2])
        transaction_id = self._unpack_int32(payload[2:6])
        ptp_args = []
        index = 6
        while index < len(payload):
            ptp_args.append(self._unpack_int32(payload[index:index + 4]))
            index += 4

        if DEBUG:
            print('PTP Response: 0x%04X' % ptp_res)
        if DEBUG2:
            self._print_args(ptp_args)
            print('[Payl]', end=" ")
            self._print_packet(ptp_payload)

        return ptp_res, ptp_args, ptp_payload

    def _wait_ptp_event(self, sock):
        sock.settimeout(0.5)
        cmd_id, payload = self._receive_response(sock)
        if cmd_id != 8:
            return 0, None

        # Event
        ptp_event = self._unpack_int16(payload[0:2])
        transaction_id = self._unpack_int32(payload[2:6])
        ptp_args = []
        index = 6
        while index < len(payload):
            ptp_args.append(self._unpack_int32(payload[index:index + 4]))
            index += 4

        return ptp_event, ptp_args

    def _send_command(self, sock, cmd_id, payload):
        packet = ''
        packet += self._pack_int32(len(payload) + 8)
        packet += self._pack_int32(cmd_id)
        packet += payload

        if DEBUG2:
            print('[SEND]', end=" ")
            self._print_packet(packet)

        sock.send(packet)

    def _receive_response(self, sock):
        packet = ''
        # packet length
        try:
            recv_data = sock.recv(4)
        except KeyboardInterrupt:
            pass
        except:
            if DEBUG:
                print('.') # recv timeout
            return -1, None
        if recv_data is None or len(recv_data) != 4:
            return 0, None
        packet_len = self._unpack_int32(recv_data)
        if DEBUG2:
            print('recv packet len = %d' % packet_len)
        if packet_len < 8:
            return 0, None
        packet += recv_data

        # command
        try:
            recv_data = sock.recv(4)
        except KeyboardInterrupt:
            pass
        except:
            if DEBUG:
                print('recv timeout, len=%d' % packet_len)
            return -1, None
        if recv_data is None or len(recv_data) != 4:
            return 0, None
        cmd_id = self._unpack_int32(recv_data)
        if DEBUG2:
            print('recv cmd id = %d' % cmd_id)
        packet += recv_data

        # payload
        packet_len -= 8
        if packet_len == 0:
            recv_data = None
        else:
            try:
                recv_data = sock.recv(packet_len)
            except:
                if DEBUG:
                    print('recv timeout, len=%d, cmd=%d' % (packet_len + 8,
                                                            cmd_id))
                    return -1, None
            if recv_data is None or len(recv_data) != packet_len:
                return 0, None
            packet += recv_data

        if DEBUG2:
            print('[RECV]', end=" ")
            self._print_packet(packet)

        return cmd_id, recv_data

    def _print_packet(self, packet):
        tab_index = 1
        for ch in packet:
            print('%02X' % ord(ch), end=" ")
            if (tab_index % 8) == 0:
                print('\n      ', end=" ")
            tab_index += 1
        print('')

    def _print_args(self, args):
        print('%d ARGS' % len(args))
        index = 0
        for arg in args:
            print('[ARGS %d] 0x%08X' % (index, arg))
            index += 1

    def _pack_guid(self):
        data = ''
        for val in self.GUID.split('-'):
            index = 0
            while index < len(val):
                data += chr(int(val[index:index + 2], 16))
                index += 2
        return data

    def _unpack_guid(self, packet):
        guid = ''
        index = 0
        for ch in packet:
            if index == 4 or index == 6 or index == 8 or index == 10:
                guid += '-'
            guid += '%02x' % ord(ch)
            index += 1
        return guid

    def _pack_string(self, str):
        data = ''
        for ch in str:
            data += ch
            data += '\x00'
        data += '\x00'
        data += '\x00'
        return data

    def _unpack_string(self, packet):
        string = ''
        index = 0
        for ch in packet:
            if (index & 1) == 0:
                string += ch
            index += 1
        return string

    def _unpack_int32(self, payload):
        return struct.unpack('<I', payload)[0]

    def _pack_int32(self, val):
        return struct.pack('<I', val)

    def _unpack_int16(self, payload):
        return struct.unpack('<H', payload)[0]

    def _pack_int16(self, val):
        if val < 0:
            val = 0x10000 + val
        return struct.pack('<H', val)

    def _unpack_int32_array(self, payload):
        num_items = self._unpack_int32(payload[0:4])
        if num_items == 0 or (num_items * 4) > (len(payload) - 4):
            return []
        items = []
        index = 4
        while index < len(payload):
            items.append(self._unpack_int32(payload[index:index+4]))
            index += 4
        return items

    def _unpack_ptp_string(self, payload):
        length = ord(payload[0])
        if length == 0:
            return ''
        end = (length * 2 - 1)
        return self._unpack_string(payload[1:end])

    def _unpack_object_info(self, payload):
        info = {}
        info['StorageID'] = self._unpack_int32(payload[0:4])
        info['ObjectFormat'] = self._unpack_int16(payload[4:6])
        info['ProtectionStatus'] = self._unpack_int16(payload[6:8])
        info['ObjectCompressedSize'] = self._unpack_int32(payload[8:12])
        info['ThumbFormat'] = self._unpack_int16(payload[12:14])
        info['ThumbCompressedSize'] = self._unpack_int32(payload[14:18])
        info['ThumbPixWidth'] = self._unpack_int32(payload[18:22])
        info['ThumbPixHeight'] = self._unpack_int32(payload[22:26])
        info['ImagePixWidth'] = self._unpack_int32(payload[26:30])
        info['ImagePixHeight'] = self._unpack_int32(payload[30:34])
        info['ImageBitDepth'] = self._unpack_int32(payload[34:38])
        info['ParentObject'] = self._unpack_int32(payload[38:42])
        info['AssociationType'] = self._unpack_int16(payload[42:44])
        info['AssociationDesc'] = self._unpack_int32(payload[44:48])
        info['SequenceNumber'] = self._unpack_int32(payload[48:52])
        index = 52
        info['Filename'] = self._unpack_ptp_string(payload[index:])
        index += ord(payload[index]) * 2 + 1
        info['CaputureDate'] = self._unpack_ptp_string(payload[index:])
        index += ord(payload[index]) * 2 + 1
        info['ModificationDate'] = self._unpack_ptp_string(payload[index:])
        index += ord(payload[index]) * 2 + 1
        info['Keywords'] = self._unpack_ptp_string(payload[index:])
        return info

class Theta360(PTP_IP):
    def __init__(self):
        '''Initialize'''
        PTP_IP.__init__(self, '192.168.1.1',
                        'THETA', '8a7ab04f-ebda-4f33-8649-8bf8c1cdc838')

    def start(self):
        return self._open_connection() and self._open_session()

    def close(self):
        self._close_session()
        self._close_connection()

    # set EV shift
    # EV shift: 2000,1700,1300,1000,700,300,0,-300,-700,-1000,-1300,-1700,-2000
    def set_ev_shift(self, ev_shift):
        self._set_device_prop_value(0x5010, self._pack_int16(ev_shift))

    def shutter(self):
        self._initiate_capture()
        self.prepare()

    def prepare(self):
        ids = self._get_storage_ids()
        if ids:
            self._handles = self._get_object_handles(ids[0])

    @property
    def num_files(self):
        ids = self._get_storage_ids()
        if ids:
            return self._get_num_objects(ids[0])
        else:
            return 0

    @property
    def info(self):
        info = self._get_object_info(self._handles[-1])
        if DEBUG:
            print('filename: %s' % info['Filename'])
            print('object format: 0x%04X' % info['ObjectFormat'])
            print('object size: %d' % info['ObjectCompressedSize'])
            print('thumbnail size: %d' % info['ThumbCompressedSize'])
            print('seq. no.: %d' % info['SequenceNumber'])
            print('capture date: %s' % info['CaputureDate'])
        return info

    @property
    def thumbnail(self):
        return self._get_thumb(self._handles[-1])

    @property
    def image(self):
        return self._get_object(self._handles[-1])

    def write_local(self, filename, image):
        with open(filename, 'wb') as f:
            f.write(image)

    def __enter__(self):
        while not self.start():
            pass
        self.prepare()
        return self

    def __exit__(self, type, value, traceback):
        self.close()


# Sample: shutter & download image to PC
if __name__ == '__main__':
    args = sys.argv[1:]
    #print(args)

    with Theta360() as theta:
        if "shutter" in args:
            #print("Taking picture")
            theta.shutter()
            #print("Took picture")

        # Download image
        if "download" in args:
            #print("Will download", end=" ")
            if "thumb" in args:
                target = theta.thumbnail
                #print("the latest thumbnail", end=" ")
            elif "image" in args:
                target = theta.image
                #print("the latest image", end=" ")

            if "auto" in args:
                filename = theta.info['Filename']
            else:
                filename = args[-1]
            #print("to {}".format(filename))
            print(filename)

            theta.write_local(filename, target)
            #print("Downloaded")

    print("Done!")
