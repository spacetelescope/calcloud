from calcloud import hst

IPPPSSOOT_INSTR = {
    "J": "acs",
    "U": "wfpc2",
    "V": "hsp",
    "W": "wfpc",
    "X": "foc",
    "Y": "fos",
    "Z": "hrs",
    "E": "eng",
    "F": "fgs",
    "I": "wfc3",
    "N": "nicmos",
    "O": "stis",
    "L": "cos",
}

INSTRUMENTS = set(IPPPSSOOT_INSTR.values())

def test_get_instrument_output_path():

    output_uri = "s3://tmp/test/output/path"

    for i in IPPPSSOOT_INSTR.keys():

        ipst = f"{i.lower()}pppssoot"

        inst = hst.get_instrument(ipst)
        output_path = hst.get_output_path(output_uri,ipst)

        correct_inst = IPPPSSOOT_INSTR.get(i)
        correct_output_path = f"{output_uri}/{inst}/{ipst}"

        assert inst == correct_inst
        assert output_path == correct_output_path
    
    for i in INSTRUMENTS:
        inst = hst.get_instrument(i)
        assert inst == i
