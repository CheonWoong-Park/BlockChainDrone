require("@nomicfoundation/hardhat-toolbox");

module.exports = {
  solidity: "0.8.28",   // 0.8.19 -> 0.8.28 로 수정
  networks: {
    localhost: {
      url: "http://127.0.0.1:8545",
      chainId: 31337
    }
  }
};

