require('dotenv').config();
require("@nomicfoundation/hardhat-toolbox");

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: "0.8.0",
  paths: {
    sources: "./contracts",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts"
  },
  networks: {
    sepolia: {
      url: "https://sepolia.infura.io/v3/6208bf4e60164822867e32cc1f608e49",
      accounts: [`0x${process.env.PRIVATE_KEY}`]
    }
  }
};
