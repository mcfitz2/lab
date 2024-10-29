from prefect import flow

from extract_and_re_upload import extract_and_re_upload
from load_location_history import load_location_history


@flow(log_prints=True)
def takeout_master():
    extract_and_re_upload()
    load_location_history()


if __name__ == "__main__":
    takeout_master.serve(name="takeout-master", cron="0 10 * * *")
