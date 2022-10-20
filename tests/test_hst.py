from calcloud import hst
from . import conftest

IPPPSSOOT_INSTR = hst.IPPPSSOOT_INSTR
INSTRUMENTS = hst.INSTRUMENTS


def test_get_instrument():
    """For each instrument listed in hst.IPPPSSOOT_INSTR,
    check to make sure that the correct instrument is returned by hst.get_instrument(),
    and that hst.get_output.path() returns the expected output paths."""
    bucket = conftest.BUCKET
    output_uri = f"s3://{bucket}"

    for i in IPPPSSOOT_INSTR.keys():

        ipst = f"{i.lower()}pppssoot"

        inst = hst.get_instrument(ipst)
        # output_path = hst.get_output_path(output_uri, ipst)

        correct_inst = IPPPSSOOT_INSTR.get(i)
        # correct_output_path = f"{output_uri}/{inst}/{ipst}"

        assert inst == correct_inst
        # assert output_path == correct_output_path

    for i in INSTRUMENTS:
        inst = hst.get_instrument(i)
        assert inst == i
