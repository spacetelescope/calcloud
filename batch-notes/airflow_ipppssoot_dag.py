from airflow import DAG

from hstdputils import airflow_dagger as dagger

PLANS = [
    ('s3://jmiller-hstdp-output', 'batch-17-2020-01-31T22-18-19/O8JHG2NNQ', 'O8JHG2NNQ', 'stis', 'hstdp-process', 1, 512, 300),
    ('s3://jmiller-hstdp-output', 'batch-17-2020-01-31T22-18-19/O8T9JEHXQ', 'O8T9JEHXQ', 'stis', 'hstdp-process', 1, 512, 300),
    ('s3://jmiller-hstdp-output', 'batch-17-2020-01-31T22-18-19/O4QPKTDCQ', 'O4QPKTDCQ', 'stis', 'hstdp-process', 1, 512, 300),
    ('s3://jmiller-hstdp-output', 'batch-17-2020-01-31T22-18-19/O6DCAQK9Q', 'O6DCAQK9Q', 'stis', 'hstdp-process', 1, 512, 300),
    ('s3://jmiller-hstdp-output', 'batch-17-2020-01-31T22-18-19/O5IA4DVMQ', 'O5IA4DVMQ', 'stis', 'hstdp-process', 1, 512, 300),
    ('s3://jmiller-hstdp-output', 'batch-17-2020-01-31T22-18-19/OBPW013H0', 'OBPW013H0', 'stis', 'hstdp-process', 1, 512, 300),
    ('s3://jmiller-hstdp-output', 'batch-17-2020-01-31T22-18-19/OBGU06030', 'OBGU06030', 'stis', 'hstdp-process', 1, 512, 300),
    ('s3://jmiller-hstdp-output', 'batch-17-2020-01-31T22-18-19/O8L7SWS9Q', 'O8L7SWS9Q', 'stis', 'hstdp-process', 1, 512, 300),
    ('s3://jmiller-hstdp-output', 'batch-17-2020-01-31T22-18-19/OCTKA6010', 'OCTKA6010', 'stis', 'hstdp-process', 1, 512, 300),
    ('s3://jmiller-hstdp-output', 'batch-17-2020-01-31T22-18-19/OA8B010B0', 'OA8B010B0', 'stis', 'hstdp-process', 1, 512, 300),
    ('s3://jmiller-hstdp-output', 'batch-17-2020-01-31T22-18-19/OBKK45010', 'OBKK45010', 'stis', 'hstdp-process', 1, 512, 300),
    ('s3://jmiller-hstdp-output', 'batch-17-2020-01-31T22-18-19/O69H2UBJQ', 'O69H2UBJQ', 'stis', 'hstdp-process', 1, 512, 300),
    ('s3://jmiller-hstdp-output', 'batch-17-2020-01-31T22-18-19/OCO603010', 'OCO603010', 'stis', 'hstdp-process', 1, 512, 300),
    ('s3://jmiller-hstdp-output', 'batch-17-2020-01-31T22-18-19/OD0T5QSYQ', 'OD0T5QSYQ', 'stis', 'hstdp-process', 1, 512, 300),
    ('s3://jmiller-hstdp-output', 'batch-17-2020-01-31T22-18-19/OBC405010', 'OBC405010', 'stis', 'hstdp-process', 1, 512, 300),
    ('s3://jmiller-hstdp-output', 'batch-17-2020-01-31T22-18-19/O4DV020A0', 'O4DV020A0', 'stis', 'hstdp-process', 1, 512, 300),
    ('s3://jmiller-hstdp-output', 'batch-17-2020-01-31T22-18-19/O60309CHQ', 'O60309CHQ', 'stis', 'hstdp-process', 1, 512, 300),
    ('s3://jmiller-hstdp-output', 'batch-17-2020-01-31T22-18-19/O62CBCURQ', 'O62CBCURQ', 'stis', 'hstdp-process', 1, 512, 300),
    ('s3://jmiller-hstdp-output', 'batch-17-2020-01-31T22-18-19/O5GJ0ZHYQ', 'O5GJ0ZHYQ', 'stis', 'hstdp-process', 1, 512, 300),
    ('s3://jmiller-hstdp-output', 'batch-17-2020-01-31T22-18-19/O4XCL7WKQ', 'O4XCL7WKQ', 'stis', 'hstdp-process', 1, 512, 300),
]

for plan in PLANS:
    varname = plan[1].replace("-","_").replace("/","_")
    dagvars, dag, operator = dagger.get_airflow_objs(plan)
    globals()[varname + "_dagvars"] = dagvars
    globals()[varname + "_dag"] = dag
    globals()[varname + "_operator"] = operator


    
