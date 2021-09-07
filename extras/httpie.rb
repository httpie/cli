# The latest Homebrew formula as submitted to Homebrew/homebrew-core.
# Only useful for testing until it gets accepted by homebrew maintainers.
# (It will need to be updated from the repo version before next release.)
#
# https://github.com/Homebrew/homebrew-core/blob/master/Formula/httpie.rb
#
class Httpie < Formula
  include Language::Python::Virtualenv

  desc "User-friendly cURL replacement (command-line HTTP client)"
  homepage "https://httpie.io/"
  url "https://files.pythonhosted.org/packages/90/64/7ea8066309970f787653bdc8c5328272a5c4d06cbce3a07a6a5c3199c3d7/httpie-2.5.0.tar.gz"
  sha256 "fe6a8bc50fb0635a84ebe1296a732e39357c3e1354541bf51a7057b4877e47f9"
  license "BSD-3-Clause"
  head "https://github.com/httpie/httpie.git"

  bottle do
    sha256 cellar: :any_skip_relocation, arm64_big_sur: "a0c123788163512698a0d284cfd6cb8125d8355aa59c3e4639df90b4388f94b5"
    sha256 cellar: :any_skip_relocation, big_sur:       "4e4bc9dd47e194bd45e9c0e36039942aed76a465871980924f0f27e83681d918"
    sha256 cellar: :any_skip_relocation, catalina:      "72dfebccff912bdb3913860983faf59c07c74db737ad4bf56143713236803821"
    sha256 cellar: :any_skip_relocation, mojave:        "4733686b9a1564835b6662e758dd39dd80fcb940b684af57485392bb9d6bf04e"
    sha256 cellar: :any_skip_relocation, x86_64_linux:  "914d67f6d9f732a7888ba2e35cf9c00525fb24917b6610544125b7bba545c7fc"
    sha256 cellar: :any_skip_relocation, high_sierra:   "87e7348b6fb40fd8e4f7597937952469601962189e62d321b8cb4fa421e035ef"
  end

  depends_on "python@3.9"

  resource "certifi" do
    url "https://files.pythonhosted.org/packages/6d/78/f8db8d57f520a54f0b8a438319c342c61c22759d8f9a1cd2e2180b5e5ea9/certifi-2021.5.30.tar.gz"
    sha256 "2bbf76fd432960138b3ef6dda3dde0544f27cbf8546c458e60baf371917ba9ee"
  end

  resource "charset-normalizer" do
    url "https://files.pythonhosted.org/packages/e7/4e/2af0238001648ded297fb54ceb425ca26faa15b341b4fac5371d3938666e/charset-normalizer-2.0.4.tar.gz"
    sha256 "f23667ebe1084be45f6ae0538e4a5a865206544097e4e8bbcacf42cd02a348f3"
  end

  resource "defusedxml" do
    url "https://files.pythonhosted.org/packages/0f/d5/c66da9b79e5bdb124974bfe172b4daf3c984ebd9c2a06e2b8a4dc7331c72/defusedxml-0.7.1.tar.gz"
    sha256 "1bb3032db185915b62d7c6209c5a8792be6a32ab2fedacc84e01b52c51aa3e69"
  end

  resource "idna" do
    url "https://files.pythonhosted.org/packages/cb/38/4c4d00ddfa48abe616d7e572e02a04273603db446975ab46bbcd36552005/idna-3.2.tar.gz"
    sha256 "467fbad99067910785144ce333826c71fb0e63a425657295239737f7ecd125f3"
  end

  resource "Pygments" do
    url "https://files.pythonhosted.org/packages/b7/b3/5cba26637fe43500d4568d0ee7b7362de1fb29c0e158d50b4b69e9a40422/Pygments-2.10.0.tar.gz"
    sha256 "f398865f7eb6874156579fdf36bc840a03cab64d1cde9e93d68f46a425ec52c6"
  end

  resource "PySocks" do
    url "https://files.pythonhosted.org/packages/bd/11/293dd436aea955d45fc4e8a35b6ae7270f5b8e00b53cf6c024c83b657a11/PySocks-1.7.1.tar.gz"
    sha256 "3f8804571ebe159c380ac6de37643bb4685970655d3bba243530d6558b799aa0"
  end

  resource "requests" do
    url "https://files.pythonhosted.org/packages/e7/01/3569e0b535fb2e4a6c384bdbed00c55b9d78b5084e0fb7f4d0bf523d7670/requests-2.26.0.tar.gz"
    sha256 "b8aa58f8cf793ffd8782d3d8cb19e66ef36f7aba4353eec859e74678b01b07a7"
  end

  resource "requests-toolbelt" do
    url "https://files.pythonhosted.org/packages/28/30/7bf7e5071081f761766d46820e52f4b16c8a08fef02d2eb4682ca7534310/requests-toolbelt-0.9.1.tar.gz"
    sha256 "968089d4584ad4ad7c171454f0a5c6dac23971e9472521ea3b6d49d610aa6fc0"
  end

  resource "urllib3" do
    url "https://files.pythonhosted.org/packages/4f/5a/597ef5911cb8919efe4d86206aa8b2658616d676a7088f0825ca08bd7cb8/urllib3-1.26.6.tar.gz"
    sha256 "f57b4c16c62fa2760b7e3d97c35b255512fb6b59a259730f36ba32ce9f8e342f"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    raw_url = "https://raw.githubusercontent.com/Homebrew/homebrew-core/HEAD/Formula/httpie.rb"
    assert_match "PYTHONPATH", shell_output("#{bin}/http --ignore-stdin #{raw_url}")
  end
end
