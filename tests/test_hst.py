from calcloud import hst
from . import conftest

# from . import conftest

IPPPSSOOT_INSTR = hst.IPPPSSOOT_INSTR
INSTRUMENTS = hst.INSTRUMENTS


def test_hst_get_instrument():
    """For each instrument listed in hst.IPPPSSOOT_INSTR,
    check to make sure that the correct instrument is returned by hst.get_instrument(),
    and that hst.get_output.path() returns the expected output paths."""
    # bucket = conftest.BUCKET
    # output_uri = f"s3://{bucket}"

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


def test_hst_is_dataset_name():
    good_dataset_names = conftest.TEST_DATASET_NAMES
    for dataset in good_dataset_names:
        is_dataset = hst.is_dataset_name(dataset)
        assert is_dataset is True

    bad_dataset_name = "nothstdataset"
    assert hst.is_dataset_name(bad_dataset_name) is False


def test_hst_get_dataset_type():
    ipst = "oekva6i8j"
    svm = "wfc3_el3_1n"
    mvm = "skycell-p0048x17y14"

    dataset_type1 = hst.get_dataset_type(ipst)
    assert dataset_type1 == "ipst"

    dataset_type2 = hst.get_dataset_type(svm)
    assert dataset_type2 == "svm"

    dataset_type3 = hst.get_dataset_type(mvm)
    assert dataset_type3 == "mvm"
