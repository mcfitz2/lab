from prefect import flow

from extract_and_re_upload import extract_and_re_upload


@flow(log_prints=True)
def instagram_master():
    extract_and_re_upload()


if __name__ == "__main__":
    instagram_master.serve(name="instagram-master", cron="0 2 * * *")
