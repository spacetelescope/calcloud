from drizzlepac.hlautils.astroquery_utils import retrieve_observation
import argparse
import sys

parser=argparse.ArgumentParser()
parser.add_argument(dest='ipst',help='the ipppssoot to retrieve from MAST', type=str)
args = parser.parse_args()


ipst = args.ipst.lower()
if ipst[0] not in ['j','i','l','o']:
    print('ipppssoot not valid because it does not start with i,j,l,o')
    sys.exit()

if ipst[0] in ('j','i'):
    filetypes=['ASN','RAW']
    retrieve_observation(ipst, suffix=filetypes)

if ipst[0] == 'o':
    filetypes = ['ASN','RAW','EPC','TAG','WAV']
    retrieve_observation(ipst, suffix=filetypes)

if ipst[0] == 'l':
    filetypes=['ASN','EPC','RAW','RAWACCUM','RAWACCUM_A','RAWACCUM_B','RAWACQ','RAWTAG','RAWTAG_A','RAWTAG_B']
    retrieve_observation(ipst, suffix=filetypes)

