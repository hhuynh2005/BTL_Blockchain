const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("TokenValuation Smart Contract", function () {
  let tokenValuation;
  let owner, oracle, user;
  const sampleToken = "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984"; // UNI
  const sampleValuationUSD = 1250000000; // 12.50 USD with 8 decimals

  beforeEach(async function () {
    [owner, oracle, user] = await ethers.getSigners();
    const TokenValuation = await ethers.getContractFactory("TokenValuation");
    tokenValuation = await TokenValuation.deploy();
    await tokenValuation.waitForDeployment();
  });

  it("Nguoi deploy phai la chu so huu (owner)", async function () {
    expect(await tokenValuation.owner()).to.equal(owner.address);
  });

  it("Owner co the cap nhat dinh gia va emit event ValuationUpdated", async function () {
    await expect(tokenValuation.setValuation(sampleToken, sampleValuationUSD))
      .to.emit(tokenValuation, "ValuationUpdated");

    const record = await tokenValuation.getValuation(sampleToken);
    expect(record.value).to.equal(sampleValuationUSD);
  });

  it("Nguoi dung binh thuong khong duoc phep cap nhat gia", async function () {
    await expect(
      tokenValuation.connect(user).setValuation(sampleToken, sampleValuationUSD)
    ).to.be.revertedWith("TokenValuation: caller is not an authorized oracle");
  });
});
