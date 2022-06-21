"""Role testing files using testinfra."""
import re


def umask_to_octal(umask):
    return int(umask, 8)


def test_users(host):
    user = host.user('container')
    assert user.exists
    assert user.shell == '/bin/bash'
    assert user.home == '/home/container'

    linger = host.file("/var/lib/systemd/linger/container")
    assert linger.exists
    assert linger.is_file


def test_filesystem(host):
    opt_container = host.file('/opt/container')
    assert opt_container.exists
    assert opt_container.is_directory
    assert opt_container.user == 'container'
    assert opt_container.group == 'container'
    assert opt_container.mode == umask_to_octal('0750')


def test_packages(host):
    print(host.system_info.distribution)
    if host.system_info.distribution in ["debian", "ubuntu"]:
        assert host.package("apt-transport-https").is_installed
        assert host.package("ca-certificates").is_installed
        assert host.package("curl").is_installed
        assert host.package("dbus-user-session").is_installed
        assert host.package("fuse-overlayfs").is_installed
        assert host.package("iptables").is_installed
        assert host.package("lvm2").is_installed
        assert host.package("uidmap").is_installed
    elif host.system_info.distribution in ["centos", "redhat", "rocky"]:
        assert host.package("dbus-daemon").is_installed
        assert host.package("fuse-overlayfs").is_installed
        assert host.package("iptables").is_installed
        assert host.package("lvm2").is_installed
        assert host.package("shadow-utils").is_installed
    else:
        assert False


def test_kernel_parameters(host):
    print(host.system_info.distribution)
    if host.system_info.distribution in ["debian", "ubuntu"]:
        assert host.sysctl("kernel.unprivileged_userns_clone") == 1
    # elif host.system_info.distribution in ["centos", "redhat", "rocky"]:
        # sysctl: cannot stat /proc/sys/fs/may_detach_mounts: No such file or directory
        # assert host.sysctl("fs.may_detach_mounts") == 1

    assert host.sysctl("net.bridge.bridge-nf-call-iptables") == 1
    assert host.sysctl("net.bridge.bridge-nf-call-ip6tables") == 1
    assert host.sysctl("net.core.netdev_max_backlog") == 32768
    assert host.sysctl("net.core.somaxconn") == 32768
    assert host.sysctl("net.ipv4.ip_forward") == 1
    assert host.sysctl("net.ipv4.ping_group_range") == "0\t2147483647"
    assert host.sysctl("net.ipv4.tcp_keepalive_time") == 1800
    assert host.sysctl("net.ipv4.tcp_max_syn_backlog") == 65536
    assert host.sysctl("net.netfilter.nf_conntrack_tcp_timeout_established") == 7200
    assert host.sysctl("net.netfilter.nf_conntrack_max") == 262140
    assert host.sysctl("user.max_user_namespaces") == 28633
    assert host.sysctl("vm.max_map_count") == 262144
    assert host.sysctl("vm.swappiness") == 1


def test_kernel_modules(host):
    file = host.file("/etc/modules-load.d/container.conf")

    assert file.exists
    assert file.is_file
    assert file.content_string == """br_netfilter
ip_conntrack
ip_tables
overlay
"""


def test_services(host):
    user_service_d = host.file("/etc/systemd/system/user@.service.d")
    assert user_service_d.exists
    assert user_service_d.is_directory

    delegate_conf = host.file("/etc/systemd/system/user@.service.d/delegate.conf")
    assert delegate_conf.exists
    assert delegate_conf.is_file
    assert delegate_conf.content_string == """[Service]
Delegate=cpu cpuset io memory pids"""

    systemd_version = host.package("systemd").version
    systemd_major_version = re.search(r'\d+', systemd_version).group()
    systemd_major_version = int(systemd_major_version)
    if systemd_major_version < 240:
        user_slice = host.file("/etc/systemd/system/user-0.slice")
        assert user_slice.exists
        assert user_slice.is_file
        assert user_slice.content_string == """[Unit]
Before=systemd-logind.service

[Slice]
Slice=user.slice

[Install]
WantedBy=multi-user.target"""

        user_slice_d = host.file("/etc/systemd/system/user-.slice.d")
        assert user_slice_d.exists
        assert user_slice_d.is_directory

        slice_override = host.file("/etc/systemd/system/user-.slice.d/override.conf")
        assert slice_override.exists
        assert slice_override.is_file
        assert slice_override.content_string == """[Slice]
Slice=user.slice
CPUAccounting=yes
MemoryAccounting=yes
IOAccounting=yes
TasksAccounting=yes"""


def test_bootloader(host):
    with host.sudo():
        cgroup_controllers = host.file("/sys/fs/cgroup/cgroup.controllers")
        assert cgroup_controllers.exists
        assert cgroup_controllers.is_file

        grub = host.file("/etc/default/grub")
        assert grub.exists
        assert grub.is_file
        assert "cgroup_enable=memory" in grub.content_string
        assert "cgroup.memory=nokmem" in grub.content_string
        assert "swapaccount=1" in grub.content_string
        assert "systemd.unified_cgroup_hierarchy=1" in grub.content_string
