import sys
import datetime
from collections import namedtuple

from hstdputils import process

# ----------------------------------------------------------------------

def get_batch_name(name):
    when = datetime.datetime.now().isoformat()
    when = when.replace(":","-")
    when = when.replace(".","-")
    return name + "-" + when[:-7]   # drop subseconds

IdInfo = namedtuple("IdInfo", ["ipppssoot", "instrument", "executable", "cpus", "memory", "max_seconds"])

JOB_INFO = {
    "acs" : ("acs", "hstdp-process", 4, 2*1024, 60*60*6),
    "cos" : ("cos", "hstdp-process", 1, 2*1024, 60*20),
    "stis" : ("stis", "hstdp-process", 1, 1*512, 60*20),
    "wfc3" : ("wfc3", "hstdp-process", 4, 2*1024, 60*60*6),
    }

def id_info(ipppssoot):
    """Given an HST IPPPSSOOT ID,  return information used to schedule it as a batch job.

    Conceptually resource requirements can be tailored to individual IPPPSSOOTs driven
    by a database lookup.

    Returns:  (ipppssoot, instrument, executable, cpus, memory, max_seconds)
    """
    instr = process.get_instrument(ipppssoot)
    return IdInfo(*(ipppssoot,)+JOB_INFO[instr])

def planner(ipppssoots_file,  output_bucket, batch_name):
    """Given an S3 `output_bucket` name string, a `batch_name` string,
    and a list of IPPPSSOOT dataset IDs `ipppssoots`, planner() will
    generate one job tuple per IPPPSSOOT.

    The job tuples define key parameters such as:

    - Where to put outputs:  's3://jmiller-hstdp-output',   batch-10-2020-01-31T14-48-20/O8JHG2NNQ'
    - How to name jobs:  'batch-10-2020-01-31T14-48-20/O8JHG2NNQ'
    - The executable to run in the container: 'hstdp-process'
    - Required cores:  1
    - Required memory: 512
    - CPU seconds til kill: 300

    In the example below, the ...'s elide timestamps like
    10-2020-01-31T19-56-59 which intentionally vary for every plan.

    >>> planner('s3://jmiller-hstdp-output', 'batch-10', ['O8JHG2NNQ', 'O8T9JEHXQ', 'O4QPKTDCQ', 'O6DCAQK9Q'])  # doctest: +ELLIPSIS
    ('s3://jmiller-hstdp-output', 'batch-.../O8JHG2NNQ', 'O8JHG2NNQ', 'stis', 'hstdp-process', 1, 512, 300)
    ('s3://jmiller-hstdp-output', 'batch-.../O8T9JEHXQ', 'O8T9JEHXQ', 'stis', 'hstdp-process', 1, 512, 300)
    ('s3://jmiller-hstdp-output', 'batch-.../O4QPKTDCQ', 'O4QPKTDCQ', 'stis', 'hstdp-process', 1, 512, 300)
    ('s3://jmiller-hstdp-output', 'batch-.../O6DCAQK9Q', 'O6DCAQK9Q', 'stis', 'hstdp-process', 1, 512, 300)

    Although hstdp-process can handle multiple ipppssoots per job,
    this planner creates a new job and S3 subdir for each ipppssoot.

    """
    batch_name = get_batch_name(batch_name)
    with open(ipppssoots_file) as f:
        ipppssoots = f.read().splitlines()
    for ipppssoot in ipppssoots:
        if process.IPPPSSOOT_RE.match(ipppssoot.upper()):
            print(plan(output_bucket, batch_name, ipppssoot))
        else:
            print(ipppssoot, file=sys.stderr)

def plan(output_bucket, batch_name, ipppssoot):
    prefix = batch_name + "/" + ipppssoot
    plan = (output_bucket, prefix,) + id_info(ipppssoot)
    return plan

# ----------------------------------------------------------------------

def test():
    import doctest
    from hstdputils import plan
    return doctest.testmod(plan, optionflags=doctest.ELLIPSIS)

if __name__ == "__main__":
    if len(sys.argv) in [2, 4]:
        if sys.argv[1] == "test":
            print(test())
        else:
            ipppssoots_file = sys.argv[1]
            output_bucket = sys.argv[2]  # 's3://jmiller-hstdp-output'
            batch_name = sys.argv[3]  #  'hstdp-test-batch'
            planner(ipppssoots_file, output_bucket, batch_name)
    else:
        print("usage: python -m hstdputils.plan  <ipppssoots_file>  [<output_bucket>]  [<batch_name>]", file=sys.stderr)
