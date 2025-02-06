use prometheus_exporter::{self, prometheus::register_gauge};
use std::path::PathBuf;
use std::str::FromStr;

use clap::{Parser, Subcommand};
use directories::ProjectDirs;
use namada_sdk::chain::Epoch;
use namada_sdk::{
    address::Address,
    chain::ChainId,
    collections::HashSet,
    error::{EncodingError, Error, Result},
    io::{NamadaIo, StdIo},
    key::common::CommonPublicKey,
    masp::{fs::FsShieldedUtils, ShieldedContext},
    rpc,
    rpc::TxBroadcastData,
    signing::find_key_by_pk,
    token,
    tx::{self, ProcessTxResponse, Section, SignatureIndex, Tx},
    wallet::fs::FsWalletUtils,
    Namada, NamadaImpl,
};
use prometheus_exporter::prometheus::core::Number;
use tendermint_rpc::HttpClient;
use tendermint_rpc::Url;

#[derive(Parser)]
#[command(version, about, long_about = None)]
pub struct Cli {
    // #[arg(long)]
    // pub validator_address: Address,
    // #[arg(long)]
    // pub account_address: Address,
    #[arg(long, default_value = "namada.5f5de2dd1b88cba30586420")]
    pub chain_id: String,
    #[arg(long, default_value = base_dir())]
    pub base_dir: std::path::PathBuf,
    #[arg(long, default_value = "https://namada-rpc.mandragora.io")]
    pub rpc_url: String,
    #[arg(long, default_value = "60")]
    pub frequency: u64,
    // listen address
    // port
    // freqeuency
}
pub fn base_dir() -> String {
    let proj_dirs = ProjectDirs::from("", "", "Namada").expect("Unable to get base dir from OS");
    proj_dirs.clone().data_dir().display().to_string()
}
type NamadaCtx = NamadaImpl<HttpClient, FsWalletUtils, FsShieldedUtils, StdIo>;

pub async fn create_client(rpc_url: &str, base_dir: PathBuf, chain_id: &str) -> HttpClient {
    let url = Url::from_str(rpc_url).expect("Invalid RPC address");
    HttpClient::new(url).unwrap()

    // let wallet_dir = base_dir.clone().join(chain_id);
    // let wallet = FsWalletUtils::new(wallet_dir.clone());
    // let masp_dir = base_dir.join("./masp");

    // let shielded_ctx = ShieldedContext::new(FsShieldedUtils::new(masp_dir));
    // let std_io = StdIo;

    // NamadaImpl::new(http_client, wallet, shielded_ctx.into(), std_io)
    //     .await
    //     .expect("unable to initialize Namada context")
}

async fn fetch_epoch(client: &HttpClient) -> f64 {
    match rpc::query_epoch(client).await {
        Ok(current_epoch) => current_epoch.0.into_f64(),
        Err(e) => -1.0,
    }
}

async fn fetch_rewards(client: &HttpClient, address: Address) -> f64 {
    match rpc::query_rewards(client, &None, &address, &None).await {
        Ok(rewards) => f64::from(rewards.raw_amount().as_u32()) / 1000000.0,
        Err(e) => -1.0,
    }
}

async fn fetch_balance(client: &HttpClient, address: Address) -> f64 {
    match rpc::get_token_balance(client, &Address::decode("tnam1q9gr66cvu4hrzm0sd5kmlnjje82gs3xlfg3v6nu7").unwrap(), &address, None).await {
        Ok(rewards) => f64::from(rewards.raw_amount().as_u32()) / 1000000.0,
        Err(e) => -1.0,
    }
}

async fn fetch_balance(client: &HttpClient, address: Address) -> f64 {
    match rpc::get_token_balance(client, &Address::decode("tnam1q9gr66cvu4hrzm0sd5kmlnjje82gs3xlfg3v6nu7").unwrap(), &address, None).await {
        Ok(rewards) => f64::from(rewards.raw_amount().as_u32()) / 1000000.0,
        Err(e) => -1.0,
    }
}

#[tokio::main]
async fn main() {
    let args = Cli::parse();

    // let binding = "0.0.0.0:9186".parse().unwrap();
    // let exporter = prometheus_exporter::start(binding).unwrap();

    // let rewards = register_gauge!("namada_rewards", "claimable rewards").unwrap();
    // let balance = register_gauge!("namada_balance", "current account balance in NAM").unwrap();
    // let voting_power = register_gauge!("namada_voting_power", "current voting power").unwrap();
    // let staked = register_gauge!("namada_staked", "NAM staked to this validator").unwrap();
    // let duration = std::time::Duration::from_millis(args.frequency * 1000);

    // loop {
    let ctx = create_client(&args.rpc_url, args.base_dir.clone(), &args.chain_id).await;

    //     let guard = exporter.wait_duration(duration);
    //     println!("Fetching rewards");
    //     rewards.set(fetch_rewards(ctx, Address::decode("tnam1q9252ynj250dw9d0n96tf9yaycljmpatfvgrj0th").unwrap()).await);
    //     drop(guard);
    // }
    let validators = vec![Address::decode("tnam1q9252ynj250dw9d0n96tf9yaycljmpatfvgrj0th").unwrap(), Address::decode("tnam1q9cysu5x8rphc9w92wglzys6kd5kqt3mdvp9sxz8").unwrap()];
    for v in validators {
        println!("Rewards available {}", fetch_rewards(&ctx, v.clone()).await);
        println!("Balance available {}", fetch_balance(&ctx, v.clone()).await);
    }
    println!("Current epoch {}", fetch_epoch(&ctx).await);
}
