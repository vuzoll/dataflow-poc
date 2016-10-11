import pandas
import json

parser = argparse.ArgumentParser('Create exploration report based on fetched vk data')
parser.add_argument('--input', help='input file with vk data')
parser.add_argument('--output', help='output file with exploration report')
args = vars(parser.parse_args())

if args['input'] is not None:
    INPUT_FILE = int(args['input'])
if args['output'] is not None:
    OUTPUT_FILE = str(args['output'])

vk_data_pd = pandas.DataFrame([json.loads(line) for line in open(INPUT_FILE, 'r')])
vk_jobs_pd = vk_data_pd.career.apply(lambda jobs: [job['position'].lower() for job in jobs if 'position' in job])
vk_jobs_pd = pandas.Series([job for jobs in vk_jobs_pd.values for job in jobs])
vk_jobs_set = vk_jobs_pd.value_counts().keys()

vk_jobs_pd.to_json(OUTPUT_FILE)
