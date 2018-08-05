apt update
apt upgrade
apt install -y openssh zsh curl tsu python python-dev libjpeg-turbo-dev libcrypt-dev ndk-sysroot clang
bash -c "$(curl -fsSL https://git.io/oh-my-termux)"

mkdir -p ~/.termux/boot
echo termux-wake-lock > ~/.termux/boot/start-sshd
echo sshd >> ~/.termux/boot/start-sshd
termux-setup-storage


# https://android.stackexchange.com/questions/185230/can-i-grant-permanent-access-to-external-storage-to-an-app-in-nougat/185244
