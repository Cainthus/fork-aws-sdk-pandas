import pandas as pd
import pytest
from deltalake import DeltaTable, write_deltalake

import awswrangler as wr


@pytest.fixture(scope="session")
def storage_options():
    return {"AWS_S3_ALLOW_UNSAFE_RENAME": "TRUE"}


@pytest.mark.parametrize("s3_additional_kwargs", [None, {"ServerSideEncryption": "AES256"}])
@pytest.mark.parametrize("pyarrow_additional_kwargs", [None, {"safe": True, "deduplicate_objects": False}])
def test_read_deltalake(path, s3_additional_kwargs, pyarrow_additional_kwargs, storage_options):
    df = pd.DataFrame({"c0": [1, 2, 3], "c1": ["foo", None, "bar"], "c2": [3.0, 4.0, 5.0], "c3": [True, False, None]})
    write_deltalake(table_or_uri=path, data=df, storage_options=storage_options)

    df2 = wr.s3.read_deltalake(
        path=path, s3_additional_kwargs=s3_additional_kwargs, pyarrow_additional_kwargs=pyarrow_additional_kwargs
    )
    assert df2.equals(df)


def test_read_deltalake_versioned(path, storage_options):
    df = pd.DataFrame({"c0": [1, 2, 3], "c1": ["foo", "baz", "bar"]})
    write_deltalake(table_or_uri=path, data=df, storage_options=storage_options)
    table = DeltaTable(path, version=0, storage_options=storage_options)

    df2 = wr.s3.read_deltalake(path=path)
    assert df2.equals(df)

    df["c2"] = [True, False, True]
    write_deltalake(table_or_uri=table, data=df, mode="overwrite", overwrite_schema=True)

    df3 = wr.s3.read_deltalake(path=path, version=0)
    assert df3.equals(df.drop("c2", axis=1))

    df4 = wr.s3.read_deltalake(path=path, version=1)
    assert df4.equals(df)


def test_read_deltalake_partitions(path, storage_options):
    df = pd.DataFrame({"c0": [1, 2, 3], "c1": [True, False, True], "par0": ["foo", "foo", "bar"], "par1": [1, 2, 2]})
    write_deltalake(table_or_uri=path, data=df, partition_by=["par0", "par1"], storage_options=storage_options)

    df2 = wr.s3.read_deltalake(path=path, columns=["c0"], partitions=[("par0", "=", "foo"), ("par1", "=", "1")])
    assert df2.shape == (1, 1)
