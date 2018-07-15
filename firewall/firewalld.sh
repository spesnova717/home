#!/bin/bash

# 設定済みのルールをクリア
# ここ、もっと適切な書き方があると思う・・・
(
IFS=$'\n'; 
RULES=(`firewall-cmd --direct --get-all-rules`)

for rule in ${RULES[@]}; do
    (
    IFS=$' '
    CMD="firewall-cmd --permanent --direct --remove-rule $rule"
    eval $CMD
    )
done
)

# BLACKLISTを破棄
firewall-cmd --permanent --direct --add-rule ipv4 filter INPUT 0 -m set --match-set BLACKLIST src -j DROP

# 自ホストからのアクセスをすべて許可
firewall-cmd --permanent --direct --add-rule ipv4 filter INPUT 0 -i lo -j ACCEPT

# 1秒間に4回を超えるpingはログを記録して破棄
# ※Ping of Death攻撃対策
firewall-cmd --permanent --direct --add-chain ipv4 filter LOG_PINGDEATH
firewall-cmd --permanent --direct --add-rule ipv4 filter LOG_PINGDEATH 1 -m limit --limit 1/s --limit-burst 4 -j ACCEPT
firewall-cmd --permanent --direct --add-rule ipv4 filter LOG_PINGDEATH 1 -j LOG --log-prefix '[PINGDEATH] : ' --log-level 7
firewall-cmd --permanent --direct --add-rule ipv4 filter LOG_PINGDEATH 1 -j DROP
firewall-cmd --permanent --direct --add-rule ipv4 filter INPUT 1 -p icmp --icmp-type echo-request -j LOG_PINGDEATH

# Ping Flood攻撃対策（4回以上pingを受信した場合、以降は1秒間に1度だけ許可します。）
firewall-cmd --permanent --direct --add-rule ipv4 filter INPUT 0 -p icmp --icmp-type 8 -m length --length :85 -m limit --limit 1/s --limit-burst 4 -j ACCEPT

# flooding of RST packets, smurf attack Rejection
firewall-cmd --permanent --direct --add-rule ipv4 filter INPUT 0 -p tcp -m tcp --tcp-flags RST RST -m limit --limit 2/second --limit-burst 2 -j ACCEPT

# 全ホスト(ブロードキャストアドレス、マルチキャストアドレス)宛パケットはログを記録せずに破棄
# ※不要ログ記録防止
firewall-cmd --permanent --direct --add-rule ipv4 filter INPUT 0 -d 255.255.255.255 -j DROP
firewall-cmd --permanent --direct --add-rule ipv4 filter INPUT 0 -d 224.0.0.1 -j DROP

# 113番ポート(IDENT)へのアクセスには拒否応答
# ※メールサーバ等のレスポンス低下防止
firewall-cmd --permanent --direct --add-rule ipv4 filter INPUT 0 -p tcp --dport 113 -j REJECT --reject-with tcp-reset

#----------------------------------------------------------
# 各種サービスを公開する場合の設定(ここから)
#----------------------------------------------------------

# 外部からのSSHポートへのアクセスを日本からのみ許可（22番ポート）
firewall-cmd --permanent --direct --add-rule ipv4 filter INPUT 1 -p tcp --dport 22 -m set --match-set WHITELIST src -j ACCEPT

# 外部からのTCP80番ポート(HTTP)へのアクセスを許可
firewall-cmd --permanent --direct --add-rule ipv4 filter INPUT 1 -p tcp --dport 80 -m set --match-set WHITELIST src -j ACCEPT

# 外部からのTCP443番ポート(HTTPS)へのアクセスを許可
firewall-cmd --permanent --direct --add-rule ipv4 filter INPUT 1 -p tcp --dport 443 -m set --match-set WHITELIST src -j ACCEPT
firewall-cmd --permanent --direct --add-rule ipv4 filter INPUT 1 -p tcp --dport 3389 -m set --match-set WHITELIST src -j ACCEPT
#----------------------------------------------------------
# 各種サービスを公開する場合の設定(ここまで)
#----------------------------------------------------------

# デフォルトルール(以降のルールにマッチしなかった場合に適用するルール)設定
firewall-cmd --permanent --direct --add-rule ipv4 filter INPUT 2 -m limit --limit 1/s -j LOG --log-prefix '[INPUT] : '
firewall-cmd --permanent --direct --add-rule ipv4 filter FORWARD 1 -m limit --limit 1/s -j LOG --log-prefix '[FORWARD] : '

firewall-cmd --permanent --direct --add-rule ipv4 filter INPUT 2 -j DROP     # 受信はすべて破棄
firewall-cmd --permanent --direct --add-rule ipv4 filter OUTPUT 0 -j ACCEPT  # 送信はすべて許可
firewall-cmd --permanent --direct --add-rule ipv4 filter FORWARD 1 -j DROP   # 通過はすべて破棄

# 設定の反映
firewall-cmd --reload
