# Information related to testing

The .ids files list ipppssoot's which have been selected for development testing
and demonstration.

all.ids includes 20 randomly selected dataset IDs for each active HST instrument: ACS, COS, STIS, WFC3.

mvp.ids includes 2 IDs per instrument, one unassociated and one associated.

The .plan files are translations of the IDs into practical terms (by hstdputils.plan)
which can be submitted to AWS Batch using hstsdputils.submit.  Plans include CPU, memory,
and processing time requirements in addition to output bucket and naming properties.

