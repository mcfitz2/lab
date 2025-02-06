FROM rust:slim as build

# create a new empty shell project
RUN USER=root cargo new --bin namada_exporter
RUN apt-get update && apt-get install -y pkg-config protobuf-compiler libssl-dev
WORKDIR /namada_exporter

# copy over your manifests
COPY ./Cargo.lock ./Cargo.lock
COPY ./Cargo.toml ./Cargo.toml

# this build step will cache your dependencies
RUN cargo build --release
RUN rm src/*.rs

# copy your source tree
COPY ./src ./src

# build for release
RUN rm ./target/release/deps/namada_exporter*
RUN cargo build --release

# our final base
FROM rust:slim

# copy the build artifact from the build stage
COPY --from=build /namada_exporter/target/release/namada_exporter .

# set the startup command to run your binary
CMD ["./namada_exporter"]
