class Httpie < Formula
  include Language::Python::Virtualenv

  desc "User-friendly cURL replacement (command-line HTTP client)"
  homepage "https://httpie.io/"
  url "https://files.pythonhosted.org/packages/7b/f9/13070f19226b7db3641fb787df36bb715063abe1b8ca03fbaeca0f465d27/httpie-3.0.1.tar.gz"
  sha256 "0e9bc93ebdcdd2d32ec24b8fa46cf7e4fde9eec7a6bd0c5d0ef224f25d7466b2"
  license "BSD-3-Clause"
  head "https://github.com/httpie/httpie.git", branch: "master"

  bottle do
    sha256 cellar: :any_skip_relocation, arm64_monterey: "9d285fcfb55ce8ed787d1b01966d51e6e07f7e77c44a204695a2d6eee9c8698d"
    sha256 cellar: :any_skip_relocation, arm64_big_sur:  "743a282b475e87a4eaf11e545f761aef1b8e4bfe49eaee47251d7629a35a8ced"
    sha256 cellar: :any_skip_relocation, monterey:       "5d63ea4f47b2028b2ba68abe12a4176934193e058edd869270221b41cc946c76"
    sha256 cellar: :any_skip_relocation, big_sur:        "5a53221a680a35d1aa00cbadde279dbe4f562d22ed207c15bd4221cb8c3180f1"
    sha256 cellar: :any_skip_relocation, catalina:       "5feadb6d76f55d6f9681682e221008c282dccf0e46ae22a959b4bad2efde204a"
    sha256 cellar: :any_skip_relocation, x86_64_linux:   "d530ddbec49588b0d481f156d35f7e5bb7d3b6427d203f04750e55cd3eecc303"
  end

  depends_on "python@3.10"

  resource "certifi" do
    url "https://files.pythonhosted.org/packages/6c/ae/d26450834f0acc9e3d1f74508da6df1551ceab6c2ce0766a593362d6d57f/certifi-2021.10.8.tar.gz"
    sha256 "78884e7c1d4b00ce3cea67b44566851c4343c120abd683433ce934a68ea58872"
  end

  resource "charset-normalizer" do
    url "https://files.pythonhosted.org/packages/48/44/76b179e0d1afe6e6a91fd5661c284f60238987f3b42b676d141d01cd5b97/charset-normalizer-2.0.10.tar.gz"
    sha256 "876d180e9d7432c5d1dfd4c5d26b72f099d503e8fcc0feb7532c9289be60fcbd"
  end

  resource "defusedxml" do
    url "https://files.pythonhosted.org/packages/0f/d5/c66da9b79e5bdb124974bfe172b4daf3c984ebd9c2a06e2b8a4dc7331c72/defusedxml-0.7.1.tar.gz"
    sha256 "1bb3032db185915b62d7c6209c5a8792be6a32ab2fedacc84e01b52c51aa3e69"
  end

  resource "idna" do
    url "https://files.pythonhosted.org/packages/62/08/e3fc7c8161090f742f504f40b1bccbfc544d4a4e09eb774bf40aafce5436/idna-3.3.tar.gz"
    sha256 "9d643ff0a55b762d5cdb124b8eaa99c66322e2157b69160bc32796e824360e6d"
  end

  resource "multidict" do
    url "https://files.pythonhosted.org/packages/8e/7c/e12a69795b7b7d5071614af2c691c97fbf16a2a513c66ec52dd7d0a115bb/multidict-5.2.0.tar.gz"
    sha256 "0dd1c93edb444b33ba2274b66f63def8a327d607c6c790772f448a53b6ea59ce"
  end

  resource "Pygments" do
    url "https://files.pythonhosted.org/packages/94/9c/cb656d06950268155f46d4f6ce25d7ffc51a0da47eadf1b164bbf23b718b/Pygments-2.11.2.tar.gz"
    sha256 "4e426f72023d88d03b2fa258de560726ce890ff3b630f88c21cbb8b2503b8c6a"
  end

  resource "PySocks" do
    url "https://files.pythonhosted.org/packages/bd/11/293dd436aea955d45fc4e8a35b6ae7270f5b8e00b53cf6c024c83b657a11/PySocks-1.7.1.tar.gz"
    sha256 "3f8804571ebe159c380ac6de37643bb4685970655d3bba243530d6558b799aa0"
  end

  resource "requests" do
    url "https://files.pythonhosted.org/packages/60/f3/26ff3767f099b73e0efa138a9998da67890793bfa475d8278f84a30fec77/requests-2.27.1.tar.gz"
    sha256 "68d7c56fd5a8999887728ef304a6d12edc7be74f1cfa47714fc8b414525c9a61"
  end

  resource "requests-toolbelt" do
    url "https://files.pythonhosted.org/packages/28/30/7bf7e5071081f761766d46820e52f4b16c8a08fef02d2eb4682ca7534310/requests-toolbelt-0.9.1.tar.gz"
    sha256 "968089d4584ad4ad7c171454f0a5c6dac23971e9472521ea3b6d49d610aa6fc0"
  end

  resource "urllib3" do
    url "https://files.pythonhosted.org/packages/b0/b1/7bbf5181f8e3258efae31702f5eab87d8a74a72a0aa78bc8c08c1466e243/urllib3-1.26.8.tar.gz"
    sha256 "0e7c33d9a63e7ddfcb86780aac87befc2fbddf46c58dbb487e0855f7ceec283c"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/httpie --version")
    assert_match version.to_s, shell_output("#{bin}/https --version")
    assert_match version.to_s, shell_output("#{bin}/http --version")

    raw_url = "https://raw.githubusercontent.com/Homebrew/homebrew-core/HEAD/Formula/httpie.rb"
    assert_match "PYTHONPATH", shell_output("#{bin}/http --ignore-stdin #{raw_url}")
  end
end
