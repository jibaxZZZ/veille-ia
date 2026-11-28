// Extrait du bundle web d'Inspector la chaîne isBlockedAddress -> createPinningLookup et l'appelle hors réseau.
import { readFileSync } from "node:fs";
import { isIP } from "node:net";
const src = readFileSync(process.argv[2], "utf8");
const start = src.indexOf("const METADATA_IPV4_ADDRESSES");
const end = src.indexOf("function bareHost(");
const code = src.slice(start, end).replaceAll("/* @__PURE__ */ ", "");
class FetchTargetError extends Error {}
const isBlockedAddress = new Function("isIP", "FetchTargetError", code + "\nreturn isBlockedAddress;")(isIP, FetchTargetError);
const cases = [
  ["169.254.169.254", "IPv4 métadonnées"],
  ["::ffff:169.254.169.254", "IPv4 mappée, forme courte"],
  ["0:0:0:0:0:ffff:a9fe:a9fe", "IPv4 mappée, forme longue"],
  ["64:ff9b::a9fe:a9fe", "NAT64 64:ff9b::/96 -> 169.254.169.254"],
  ["64:ff9b::169.254.169.254", "NAT64 /96, IPv4 pointée"],
  ["64:ff9b::6464:64c8", "NAT64 /96 -> 100.100.100.200"],
  ["64:ff9b:1:a9fe:a9:fe00::", "NAT64 local 64:ff9b:1::/48 -> 169.254.169.254"],
  ["64:ff9b::808:808", "NAT64 /96 -> 8.8.8.8 (public)"],
  ["FE80::1", "lien-local en majuscules"],
  ["fd00:ec2:0:0::254", "métadonnées AWS IPv6, forme non canonique"],
  ["fd00:ec2::254", "métadonnées AWS IPv6"],
  ["2001:db8::1", "IPv6 ordinaire"],
  ["8.8.8.8", "IPv4 publique"],
];
for (const [ip, label] of cases) console.log(ip.padEnd(28), (isBlockedAddress(ip) ? "BLOQUÉ" : "autorisé").padEnd(9), label);
