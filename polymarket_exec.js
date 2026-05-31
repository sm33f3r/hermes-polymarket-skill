import { ClobClient, Chain, Side, OrderType, SignatureTypeV2 } from "@polymarket/clob-client-v2";
import { createWalletClient, http } from "viem";
import { privateKeyToAccount } from "viem/accounts";
import { polygon } from "viem/chains";

const requiredEnvVars = [
  "POLYMARKET_PRIVATE_KEY", "CLOB_API_KEY", "CLOB_SECRET", "CLOB_PASS_PHRASE",
  "POLYMARKET_PROXY_ADDRESS", "CHAINSTACK_NODE"
];
for (const envVar of requiredEnvVars) {
  if (!process.env[envVar]) {
    process.stdout.write(JSON.stringify({ ok: false, error: `Missing required env var: ${envVar}` }) + "\n");
    process.exit(1);
  }
}

const privateKey = process.env.POLYMARKET_PRIVATE_KEY.startsWith("0x")
  ? process.env.POLYMARKET_PRIVATE_KEY : "0x" + process.env.POLYMARKET_PRIVATE_KEY;
const account = privateKeyToAccount(privateKey);
const walletClient = createWalletClient({ account, chain: polygon, transport: http(process.env.CHAINSTACK_NODE) });
const client = new ClobClient({
  host: "https://clob.polymarket.com", chain: Chain.POLYGON, signer: walletClient,
  creds: { key: process.env.CLOB_API_KEY, secret: process.env.CLOB_SECRET, passphrase: process.env.CLOB_PASS_PHRASE },
  signatureType: SignatureTypeV2.POLY_1271, funderAddress: process.env.POLYMARKET_PROXY_ADDRESS,
});

function respond(obj) { process.stdout.write(JSON.stringify(obj) + "\n"); }

async function main() {
  try {
    if (process.argv.length < 3) { respond({ ok: false, error: "Invalid or missing command argument" }); return; }
    const cmd = JSON.parse(process.argv[2]);

    switch (cmd.command) {
      case "balance": {
        const result = await client.getBalanceAllowance({ asset_type: "COLLATERAL" });
        respond({ ok: true, balance_usd: parseFloat(result.balance) / 1e6, raw: result });
        break;
      }
      case "positions": {
        const result = await client.getOpenOrders();
        respond({ ok: true, positions: result });
        break;
      }
      case "buy": {
        const book = await client.getOrderBook(cmd.token_id);
        if (!book.asks || book.asks.length === 0) { respond({ ok: false, error: "no asks" }); break; }

        const bestAsk = book.asks.sort((a, b) => parseFloat(a.price) - parseFloat(b.price))[0];
        const bestBid = book.bids?.length ? book.bids.sort((a, b) => parseFloat(b.price) - parseFloat(a.price))[0] : null;
        if (bestBid && (parseFloat(bestAsk.price) - parseFloat(bestBid.price)) > 0.10) {
          respond({ ok: false, error: `spread too wide: ${(parseFloat(bestAsk.price)-parseFloat(bestBid.price)).toFixed(4)}` }); break;
        }

        const roundedPrice = Math.round(Math.min(parseFloat(bestAsk.price) + 0.03, 0.97) * 100) / 100;
        // Don't pass negRisk — let the library auto-detect from the CLOB API
        const order = await client.createMarketOrder(
          { tokenID: cmd.token_id, side: Side.BUY, amount: cmd.amount_usd, price: roundedPrice },
          { tickSize: "0.01" }
        );
        const resp = await client.postOrder(order, OrderType.FAK);
        respond({ ok: true, order_id: resp.orderID, status: resp.status, price_limit: roundedPrice, size_filled: resp.sizeFilled ?? null });
        break;
      }
      case "sell": {
        const book = await client.getOrderBook(cmd.token_id);
        if (!book.bids || book.bids.length === 0) { respond({ ok: false, error: "no bids" }); break; }
        const bestBid = book.bids.sort((a, b) => parseFloat(b.price) - parseFloat(a.price))[0];
        const roundedPrice = Math.round(Math.max(parseFloat(bestBid.price) - 0.03, 0.03) * 100) / 100;
        const order = await client.createMarketOrder(
          { tokenID: cmd.token_id, side: Side.SELL, amount: cmd.amount_shares, price: roundedPrice },
          { tickSize: "0.01" }
        );
        const resp = await client.postOrder(order, OrderType.FOK);
        respond({ ok: true, order_id: resp.orderID, status: resp.status });
        break;
      }
      case "approve": {
        const result = await client.updateBalanceAllowance({ asset_type: "COLLATERAL" });
        respond({ ok: true, result });
        break;
      }
      default: respond({ ok: false, error: `Unknown command: ${cmd.command}` });
    }
  } catch (err) { respond({ ok: false, error: err.message || String(err) }); }
}
main();