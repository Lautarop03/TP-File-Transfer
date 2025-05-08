from lib.protocols.stop_and_wait import StopAndWait
from lib.protocols.selective_repeat import SelectiveRepeat
from lib.utils.constants import SELECTIVE_REPEAT, STOP_AND_WAIT


def get_protocol_name_from_protocol_code(protocol_code):
    if protocol_code == STOP_AND_WAIT:
        return 'sw'
    return 'sr'


def get_protocol_code_from_protocol_str(protocol_str):
    return STOP_AND_WAIT if protocol_str == 'sw' else SELECTIVE_REPEAT


def get_protocol_from_args(args, socket, destination_address):
    protocol = get_protocol_code_from_protocol_str(args.protocol)

    if protocol == STOP_AND_WAIT:
        return StopAndWait(
            socket,
            destination_address,
            args.verbose,
            args.quiet
        )
    else:
        return SelectiveRepeat(
            socket,
            destination_address,
            args.verbose,
            args.quiet
        )
