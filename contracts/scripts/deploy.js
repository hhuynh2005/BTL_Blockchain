const hre = require("hardhat");

async function main() {
  console.log("Bat dau deploy smart contract TokenValuation len mang Sepolia...");

  const TokenValuation = await hre.ethers.getContractFactory("TokenValuation");
  const tokenValuation = await TokenValuation.deploy();
  await tokenValuation.waitForDeployment();

  const contractAddress = await tokenValuation.getAddress();
  console.log(`Smart contract TokenValuation da duoc deploy thanh cong tai dia chi: ${contractAddress}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
