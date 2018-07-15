Machine SPEC
OS : Centos7
M/B : PRIME H270 PRO
CPU : Core i5 7600
SSD : SANDISK SSD 120GB
MEM : 8GB

新たにルールを追加したい場合は
/etc/firewalld/direct.xml を直接編集する.
firewall-cmd --reload

URL : https://qiita.com/kskiwmt/items/f871f940fa9b64b4f396

#WARNING関連
systemctl status firewalld
実行するとWARNINGが出てくる．
virbr0という仮想ブリッジが原因である．
無効化すればメッセージは消える．

# brctl show <- ブリッジ設定の確認
bridge name bridge id   STP enabled interfaces
virbr0    8000.525400de6949 yes   virbr0-nic

# virsh net-destroy default  <- 仮想ブリッジの停止
Network default destroyed

# brctl show  <- ブリッジ設定の確認
bridge name     bridge id               STP enabled     interfaces

# virsh net-list --all  <- 仮想ブリッジの自動起動設定状態を確認
 Name                 State      Autostart     Persistent
 ----------------------------------------------------------
 default              inactive   yes           yes

# virsh net-autostart default --disable  <- 仮想ブリッジの自動起動抑止
Network default unmarked as autostarted

# virsh net-list --all 
Name                 State      Autostart     Persistent
