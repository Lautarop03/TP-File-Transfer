from lib.protocols.stop_and_wait import StopAndWait
from lib.protocols.selective_repeat import SelectiveRepeat
from lib.utils.constants import SELECTIVE_REPEAT, STOP_AND_WAIT
from lib.utils.transfer_config import TransferConfig


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


def get_transfer_config_from_args(args, file_name, file_path):
    server_address = (args.host, args.port)
    return TransferConfig(
        server_address=server_address,
        file_name=file_name,
        file_path=file_path,
        # Download:
        #   - Name: Quiero file con este nombre
        #   - Path: Guardar en este path
        # Upload:
        #   - name: Nombre file en server
        #   - path: Origen archivo a subir
        # El server ya tiene su propio path...
        verbose=args.verbose,
        quiet=args.quiet
    )
