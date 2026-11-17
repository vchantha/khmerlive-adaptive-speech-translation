#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/infra/tls/generated"
MOUNT_OUT="$OUT"

# Git Bash on Windows rewrites POSIX-looking arguments (e.g. /bin/bash, /tls)
# and Docker Desktop needs a Windows-style host path for bind mounts.
if command -v cygpath >/dev/null 2>&1; then
  export MSYS_NO_PATHCONV=1
  MOUNT_OUT="$(cygpath -m "$OUT")"
fi

if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

KAFKA_TLS_PASSWORD="${KAFKA_TLS_PASSWORD:-change-me-kafka-tls}"
TLS_DAYS="${TLS_DAYS:-825}"

# Hostname or IP other machines use to reach this host (e.g. 192.168.1.20 or
# khmerlive.lan). It is added to every service certificate so remote clients
# can verify TLS. EXTRA_TLS_SANS takes extra comma-separated names/IPs.
PUBLIC_HOST="${PUBLIC_HOST:-localhost}"
EXTRA_TLS_SANS="${EXTRA_TLS_SANS:-}"

san_entry() {
  if [[ "$1" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    printf 'IP:%s' "$1"
  else
    printf 'DNS:%s' "$1"
  fi
}

PUBLIC_SANS=""
IFS=',' read -ra _hosts <<<"$PUBLIC_HOST,$EXTRA_TLS_SANS"
for h in "${_hosts[@]}"; do
  h="${h// /}"
  [[ -z "$h" || "$h" == "localhost" || "$h" == "127.0.0.1" ]] && continue
  PUBLIC_SANS="$PUBLIC_SANS,$(san_entry "$h")"
done

# The CA is kept across runs so clients that already trust it keep working;
# service certificates are always re-issued so SAN changes take effect.
# FORCE_TLS=1 regenerates everything, including the CA.
if [[ "${FORCE_TLS:-0}" == "1" ]]; then
  rm -rf "$OUT"
fi
mkdir -p "$OUT"
if [[ -f "$OUT/ca.crt" ]]; then
  echo "Reusing existing CA: $OUT/ca.crt"
fi

docker run --rm   -e HOST_UID="$(id -u)"   -e HOST_GID="$(id -g)"   -e TLS_DAYS="$TLS_DAYS"   -e KAFKA_TLS_PASSWORD="$KAFKA_TLS_PASSWORD"   -e PUBLIC_SANS="$PUBLIC_SANS"   -v "$MOUNT_OUT:/out"   alpine:3.22 sh -euc '
    apk add --no-cache openssl >/dev/null

    if [ ! -f /out/ca.crt ] || [ ! -f /out/ca.key ]; then
      openssl genrsa -out /out/ca.key 4096
      openssl req -x509 -new -sha256 -days "$TLS_DAYS"       -key /out/ca.key       -subj "/C=KH/O=KhmerLive/CN=KhmerLive Development CA"       -out /out/ca.crt
    fi

    issue_cert() {
      svc="$1"
      sans="$2"
      mkdir -p "/out/$svc"
      openssl genrsa -out "/out/$svc/tls.key" 3072
      openssl req -new -key "/out/$svc/tls.key"         -subj "/C=KH/O=KhmerLive/CN=$svc"         -out "/out/$svc/tls.csr"

      cat >"/tmp/$svc.ext" <<EOF
basicConstraints=CA:FALSE
keyUsage=digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=$sans$PUBLIC_SANS
EOF

      openssl x509 -req -sha256 -days "$TLS_DAYS"         -in "/out/$svc/tls.csr"         -CA /out/ca.crt -CAkey /out/ca.key -CAcreateserial         -extfile "/tmp/$svc.ext"         -out "/out/$svc/tls.crt"
      cp /out/ca.crt "/out/$svc/ca.crt"
      rm -f "/out/$svc/tls.csr"
    }

    issue_cert web "DNS:web,DNS:localhost,DNS:khmerlive.local,IP:127.0.0.1"
    issue_cert api "DNS:api,DNS:localhost,IP:127.0.0.1"
    issue_cert silo "DNS:silo,DNS:localhost,DNS:s3.khmerlive.local,IP:127.0.0.1"
    issue_cert kafka "DNS:kafka,DNS:localhost,IP:127.0.0.1"
    issue_cert jupyterhub "DNS:jupyterhub,DNS:localhost,IP:127.0.0.1"
    issue_cert kafka-ui "DNS:kafka-ui,DNS:localhost,IP:127.0.0.1"

    # SILO follows MinIO-compatible TLS file names.
    cp /out/silo/tls.crt /out/silo/public.crt
    cp /out/silo/tls.key /out/silo/private.key
    rm -rf /out/silo/CAs
    mkdir -p /out/silo/CAs
    cp /out/ca.crt /out/silo/CAs/ca.crt

    # Kafka server keystore.
    openssl pkcs12 -export       -in /out/kafka/tls.crt       -inkey /out/kafka/tls.key       -certfile /out/ca.crt       -name kafka       -out /out/kafka/kafka.keystore.p12       -passout pass:"$KAFKA_TLS_PASSWORD"

    chmod 600 /out/ca.key /out/*/tls.key /out/silo/private.key /out/kafka/kafka.keystore.p12
    chown -R "$HOST_UID:$HOST_GID" /out
  '

docker run --rm   --user "$(id -u):$(id -g)"   -e KAFKA_TLS_PASSWORD="$KAFKA_TLS_PASSWORD"   -v "$MOUNT_OUT:/tls"   apache/kafka:4.4.0 /bin/bash -euc '
    rm -f /tls/kafka/kafka.truststore.p12
    keytool -importcert -noprompt       -alias khmerlive-ca       -file /tls/ca.crt       -keystore /tls/kafka/kafka.truststore.p12       -storetype PKCS12       -storepass "$KAFKA_TLS_PASSWORD"
  '

cat >"$OUT/kafka/client.properties" <<EOF
security.protocol=SSL
ssl.truststore.location=/etc/kafka/secrets/kafka.truststore.p12
ssl.truststore.password=$KAFKA_TLS_PASSWORD
ssl.truststore.type=PKCS12
ssl.endpoint.identification.algorithm=https
EOF
chmod 600 "$OUT/kafka/client.properties"

echo "Generated TLS files under $OUT"
echo "Service certificates are valid for localhost${PUBLIC_SANS:+ and ${PUBLIC_SANS#,}}."
echo "For browser access, trust $OUT/ca.crt on every client machine/OS."
