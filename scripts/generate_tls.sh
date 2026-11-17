#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/infra/tls/generated"

if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

KAFKA_TLS_PASSWORD="${KAFKA_TLS_PASSWORD:-change-me-kafka-tls}"
TLS_DAYS="${TLS_DAYS:-825}"

if [[ -f "$OUT/ca.crt" && "${FORCE_TLS:-0}" != "1" ]]; then
  echo "TLS material already exists: $OUT"
  echo "Use FORCE_TLS=1 make tls to regenerate."
  exit 0
fi

rm -rf "$OUT"
mkdir -p "$OUT"

docker run --rm   -e HOST_UID="$(id -u)"   -e HOST_GID="$(id -g)"   -e TLS_DAYS="$TLS_DAYS"   -e KAFKA_TLS_PASSWORD="$KAFKA_TLS_PASSWORD"   -v "$OUT:/out"   alpine:3.22 sh -euc '
    apk add --no-cache openssl >/dev/null

    openssl genrsa -out /out/ca.key 4096
    openssl req -x509 -new -sha256 -days "$TLS_DAYS"       -key /out/ca.key       -subj "/C=KH/O=KhmerLive/CN=KhmerLive Development CA"       -out /out/ca.crt

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
subjectAltName=$sans
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

    # SILO follows MinIO-compatible TLS file names.
    cp /out/silo/tls.crt /out/silo/public.crt
    cp /out/silo/tls.key /out/silo/private.key
    mkdir -p /out/silo/CAs
    cp /out/ca.crt /out/silo/CAs/ca.crt

    # Kafka server keystore.
    openssl pkcs12 -export       -in /out/kafka/tls.crt       -inkey /out/kafka/tls.key       -certfile /out/ca.crt       -name kafka       -out /out/kafka/kafka.keystore.p12       -passout pass:"$KAFKA_TLS_PASSWORD"

    chmod 600 /out/ca.key /out/*/tls.key /out/silo/private.key /out/kafka/kafka.keystore.p12
    chown -R "$HOST_UID:$HOST_GID" /out
  '

docker run --rm   --user "$(id -u):$(id -g)"   -e KAFKA_TLS_PASSWORD="$KAFKA_TLS_PASSWORD"   -v "$OUT:/tls"   apache/kafka:4.4.0 /bin/bash -euc '
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
echo "For local browser access, trust $OUT/ca.crt in your workstation/OS."
