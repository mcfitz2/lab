use prometheus_exporter::{self, prometheus::register_gauge};
use std::str::FromStr;
use clap::{Parser};
use namada_sdk::{
    address::Address,
    rpc,
};
use namada_sdk::uint::Uint;
use prometheus_exporter::prometheus::core::{AtomicF64, GenericGauge};
use tendermint_rpc::HttpClient;
use tendermint_rpc::Url;

const NAM_ADDRESS: &str = "tnam1q9gr66cvu4hrzm0sd5kmlnjje82gs3xlfg3v6nu7";

#[derive(Parser)]
#[command(version, about, long_about = None)]
pub struct Cli {
    #[clap(short, long, value_parser, num_args = 1.., value_delimiter = ' ')]
    pub address: Vec<Address>,
    #[arg(long, default_value = "https://namada-rpc.mandragora.io")]
    pub rpc_url: String,
    #[arg(long, default_value = "6")]
    pub frequency: u64,
    #[arg(long, default_value = "127.0.0.1")]
    pub listen_address: String,
    #[arg(long, default_value = "9186")]
    pub listen_port: u32,
}

pub async fn create_client(rpc_url: &str) -> HttpClient {
    let url = Url::from_str(rpc_url).expect("Invalid RPC address");
    HttpClient::new(url).unwrap()
}


async fn fetch_rewards(client: &HttpClient, address: Address) -> f64 {
    match rpc::query_rewards(client, &None, &address, &None).await {
        Ok(rewards) => f64::from(rewards.raw_amount().as_u32()) / 1000000.0,
        Err(_e) => -1.0,
    }
}

async fn fetch_balance(client: &HttpClient, address: Address) -> f64 {
    let nam = Address::decode(NAM_ADDRESS).unwrap();

    match rpc::get_token_balance(client, &nam, &address, None).await {
        Ok(balance) => {
            f64::from(balance.raw_amount().as_u32()) / 1000000.0
        },
        Err(e) => {
            eprintln!("{}", e);
            -1.0
        },
    }
}

async fn fetch_staked(client: &HttpClient, address: Address) -> f64 {
    match rpc::query_epoch(client).await {
         Ok(epoch) => {
             match rpc::get_validator_stake(client, epoch, &address).await {
                 Ok(stake) => (stake.raw_amount().as_u64() / 1000000) as f64,
                 Err(_e) => 0.0,
             }
         }
         Err(_e) => 0.0
    }
}

async fn fetch_voting_power(client: &HttpClient, address: Address) -> f64 {
    match rpc::query_epoch(client).await {
        Ok(epoch) => {
            match rpc::get_validator_stake(client, epoch, &address).await {
                Ok(stake) => {
                    let staked = stake.raw_amount().checked_div(Uint::from(1000000)).unwrap().as_u32();
                    match rpc::get_total_active_voting_power(client, epoch).await {
                        Ok(total_voting_power) => {
                            f64::from(staked) / f64::from(total_voting_power.raw_amount().checked_div(Uint::from(1000000)).unwrap().as_u32())
                        },
                        Err(_e) => -1.0,
                    }
                },
                Err(_e) => -1.0,
            }
        }
        Err(_e) => -1.0
    }
}


struct AddressGaugeSet {
    rewards: GenericGauge<AtomicF64>,
    balance: GenericGauge<AtomicF64>,
    voting_power: GenericGauge<AtomicF64>,
    staked: GenericGauge<AtomicF64>,
    address: Address,
}
#[tokio::main]
async fn main() {
    let args = Cli::parse();
    let client = create_client(&args.rpc_url).await;
    
    let gauges = args.address.iter().map(
        |x| AddressGaugeSet {
            rewards: register_gauge!(format!("namada_{}_rewards", x), "claimable rewards").unwrap(),
            balance: register_gauge!(format!("namada_{}_balance", x), "current account balance in NAM").unwrap(),
            voting_power: register_gauge!(format!("namada_{}_voting_power", x), "current voting power").unwrap(),
            staked: register_gauge!(format!("namada_{}_staked", x), "NAM staked to this validator").unwrap(),
            address: x.clone()
        }
    ).collect::<Vec<AddressGaugeSet>>();

    let binding = "0.0.0.0:9186".parse().unwrap();
    let exporter = prometheus_exporter::start(binding).unwrap();


    let duration = std::time::Duration::from_millis(args.frequency * 1000);

    loop {

        let guard = exporter.wait_duration(duration);
        println!("Fetching metrics");
        for set in gauges.iter() {
            set.rewards.set(fetch_rewards(&client, set.address.clone()).await);
            set.balance.set(fetch_balance(&client, set.address.clone()).await);
            set.voting_power.set(fetch_voting_power(&client, set.address.clone()).await);
            set.staked.set(fetch_staked(&client, set.address.clone()).await);
        }
        drop(guard);
        println!("Fetching metrics complete");
    }
}
