# Fedora Linux
%global keyszer_user keymapper

Name:		keyszer
Version:	0.6.0
Release:	1%{?dist}
License:	GPLv3
Summary:	X keyboard remappring tool
URL:		https://github.com/joshgoebel/%{name}
Source0:	https://github.com/joshgoebel/%{name}/archive/%{name}-%{version}.tar.gz
Source1:	%{name}.service
Source2:	uinput.conf
Source3:	90-keymapper-acl.rules
Source4:	xhostplus.desktop
Source5:	keyszer.conf
BuildRequires:	pyproject-rpm-macros
BuildRequires:	systemd-rpm-macros
Requires:	acl
Requires:	xhost
BuildArch:	noarch

%description
Keyszer is a smart key remapper for Linux (and X11) written in Python.
It's similar to xmodmap but allows far more flexible remappings.


%prep
%autosetup


%generate_buildrequires
%pyproject_buildrequires -w


%build
%pyproject_wheel


%install
%pyproject_install
# 1. service
install -p -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/%{name}.service
# 2. little system fix
install -p -D -m 0644 %{SOURCE2} %{buildroot}%{_modulesloaddir}/uinput.conf
# 3. udev rules
install -p -D -m 0644 %{SOURCE3} %{buildroot}%{_udevrulesdir}/90-keymapper-acl.rules
# 4. xhost tuning
install -p -D -m 0644 %{SOURCE4} %{buildroot}%{_sysconfdir}/xdg/autostart/xhostplus.desktop
# 5. default config
install -p -D -m 0644 %{SOURCE5} %{buildroot}%{_sysconfdir}/%{name}.conf
%pyproject_save_files keyszer


%pre
getent passwd %{keyszer_user} > /dev/null || \
    useradd -r -M -N -d / -g nobody \
    -s /sbin/nologin -c "Keyszer user" %{keyszer_user}
exit 0


%post
%systemd_post %{name}.service


%preun
%systemd_preun %{name}.service


%postun
%systemd_postun %{name}.service


%files -f %{pyproject_files}
%doc README.md example/config.py
%{_bindir}/%{name}
%{_unitdir}/%{name}.service
%{_modulesloaddir}/uinput.conf
%{_udevrulesdir}/90-keymapper-acl.rules
%{_sysconfdir}/xdg/autostart/xhostplus.desktop
%config(noreplace) %{_sysconfdir}/%{name}.conf

%changelog
* Sat Jul 16 2022 TI_Eugene <ti.eugene@gmail.com> - 0.6.0-1
- Initial build
